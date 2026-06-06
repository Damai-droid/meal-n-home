# Create your models here.
from django.db import models
from django.utils import timezone
import random
import string


def generate_order_code():
    """
    Generate kode pesanan unik format ORD-YYYYMMDD-XXX.
    Contoh: ORD-20260605-001, ORD-20260605-002
    Counter di-reset tiap hari (berdasarkan tanggal hari ini).
    """
    from django.utils import timezone as tz
    today_str = tz.now().strftime('%Y%m%d')
    prefix = f'ORD-{today_str}-'

    # Hitung berapa order sudah dibuat hari ini
    from django.apps import apps
    try:
        Order = apps.get_model('core', 'Order')
        count_today = Order.objects.filter(order_code__startswith=prefix).count()
    except Exception:
        count_today = 0

    # Buat kode dengan counter 3 digit, loop jika tabrakan
    for i in range(count_today + 1, count_today + 100):
        candidate = f'{prefix}{i:03d}'
        try:
            Order = apps.get_model('core', 'Order')
            if not Order.objects.filter(order_code=candidate).exists():
                return candidate
        except Exception:
            return candidate

    # Fallback dengan random suffix jika ada ratusan order hari ini
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f'{prefix}{rand}'


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='🍽️')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    PORTION_CHOICES = [
        ('solo', 'Solo (1 orang)'),
        ('duo', 'Duo (2 orang)'),
        ('family', 'Family (4 orang)'),
        ('party', 'Party (8 orang)'),
    ]

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    portion = models.CharField(max_length=20, choices=PORTION_CHOICES, default='solo')
    price = models.DecimalField(max_digits=10, decimal_places=0)
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_bundle = models.BooleanField(default=False)
    is_seasonal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(upload_to='products/gallery/')

class Addon(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=0)
    icon = models.CharField(max_length=50, default='➕')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        ('weekly', 'Mingguan'),
        ('monthly', 'Bulanan'),
        ('quarterly', '3 Bulanan'),
    ]
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    deliveries_per_week = models.IntegerField(default=3)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=0)
    description = models.TextField()
    is_popular = models.BooleanField(default=False)

    def discount_percent(self):
        if self.original_price > 0:
            return int((1 - self.price / self.original_price) * 100)
        return 0

    def __str__(self):
        return f"{self.name} ({self.duration})"


class Bundle(models.Model):
    name = models.CharField(max_length=200)
    products = models.ManyToManyField(Product)
    bundle_price = models.DecimalField(max_digits=10, decimal_places=0)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class LoyaltyTier(models.Model):
    name = models.CharField(max_length=50)  # Bronze, Silver, Gold, Platinum
    min_points = models.IntegerField()
    discount_percent = models.IntegerField(default=0)
    color = models.CharField(max_length=20, default='#CD7F32')

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Menunggu Pembayaran'),
        ('paid', 'Sudah Dibayar'),
        ('processing', 'Diproses'),
        ('delivered', 'Dikirim'),
        ('completed', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ]
    PAYMENT_CHOICES = [
        ('transfer', 'Transfer Bank'),
        ('ewallet', 'E-Wallet (GoPay/OVO/Dana)'),
        ('cod', 'COD'),
        ('qris', 'QRIS'),
    ]

    order_code = models.CharField(max_length=20, unique=True, blank=True, db_index=True)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    bundle = models.ForeignKey(Bundle, on_delete=models.SET_NULL, null=True, blank=True)
    subscription_schedule = models.CharField(max_length=100, blank=True)
    subscription_diet = models.CharField(max_length=100, blank=True)
    addons = models.ManyToManyField(Addon, blank=True)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='transfer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    referral_code = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        import datetime
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = Order.objects.get(pk=self.pk).status
            except Order.DoesNotExist:
                pass

        if not self.order_code:
            code = generate_order_code()
            while Order.objects.filter(order_code=code).exists():
                code = generate_order_code()
            self.order_code = code
        super().save(*args, **kwargs)

        # Catat history status jika baru dibuat atau status berubah
        if is_new or old_status != self.status:
            OrderStatusHistory.objects.create(
                order=self,
                status=self.status,
                notes=f"Status pesanan diperbarui menjadi: {self.get_status_display()}"
            )

    def get_estimated_delivery(self):
        """
        Mengembalikan estimasi waktu pengiriman berdasarkan tipe order dan status.
        """
        import datetime
        if self.status == 'completed':
            return "Pesanan sudah diterima"
        elif self.status == 'cancelled':
            return "-"
            
        if self.subscription:
            schedule = self.subscription_schedule or "Senin, Rabu, Jumat"
            return f"Pengiriman rutin berikutnya sesuai jadwal: {schedule}"
        else:
            # Estimasi 45 menit dari waktu dibuat
            local_created = timezone.localtime(self.created_at)
            eta = local_created + datetime.timedelta(minutes=45)
            return eta.strftime('%d %b %Y, %H:%M WIB')

    def get_status_color(self):
        colors = {
            'pending': '#F59E0B',
            'paid': '#3B82F6',
            'processing': '#8B5CF6',
            'delivered': '#06B6D4',
            'completed': '#10B981',
            'cancelled': '#EF4444',
        }
        return colors.get(self.status, '#9CA3AF')

    def get_tracking_step(self):
        """
        Mengembalikan tuple (step_number, percentage_progress) 
        berdasarkan status pesanan saat ini untuk visualisasi progress bar.
        """
        steps = {
            'pending': (1, 0),
            'paid': (2, 25),
            'processing': (3, 50),
            'delivered': (4, 75),
            'completed': (5, 100),
            'cancelled': (0, 0),
        }
        return steps.get(self.status, (0, 0))

    def __str__(self):
        return f"Order {self.order_code} - {self.customer_name}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.order.order_code} - {self.get_status_display()} at {self.changed_at}"



class ReferralCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.IntegerField(default=10)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class SeasonalCampaign(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    discount_percent = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    banner_color = models.CharField(max_length=20, default='#E2633A')

    def is_ongoing(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    def __str__(self):
        return self.title


class Partnership(models.Model):
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name