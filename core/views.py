# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import (
    Product, Category, SubscriptionPlan, Bundle,
    Addon, Order, ReferralCode, SeasonalCampaign, Partnership
)
from .forms import OrderForm, PartnershipForm




def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah dipakai')
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        return redirect('home')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username atau password salah')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def home(request):
    # Produk unggulan (is_featured=True)
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:6]

    # Produk populer: diurutkan berdasarkan jumlah order terbanyak
    from django.db.models import Count
    popular_products = (
        Product.objects.filter(is_available=True)
        .annotate(order_count=Count('order'))
        .order_by('-order_count', '-created_at')[:6]
    )

    categories = Category.objects.all()
    subscription_plans = SubscriptionPlan.objects.all()[:3]
    bundles = Bundle.objects.filter(is_active=True)[:3]
    addons = Addon.objects.filter(is_active=True)[:6]

    # Kampanye musiman yang sedang aktif hari ini
    campaigns = SeasonalCampaign.objects.filter(is_active=True)
    active_campaigns = [c for c in campaigns if c.is_ongoing()]
    # Ambil satu kampanye aktif pertama untuk banner utama
    active_campaign = active_campaigns[0] if active_campaigns else None

    # Statistik dinamis dari database
    total_orders = Order.objects.filter(status='completed').count()
    total_menus = Product.objects.filter(is_available=True).count()

    context = {
        'featured_products': featured_products,
        'popular_products': popular_products,
        'categories': categories,
        'subscription_plans': subscription_plans,
        'bundles': bundles,
        'addons': addons,
        'active_campaigns': active_campaigns,
        'active_campaign': active_campaign,   # untuk banner tunggal di hero
        'total_orders': total_orders,
        'total_menus': total_menus,
    }
    return render(request, 'home.html', context)


def subscription(request):
    subscription_plans = SubscriptionPlan.objects.all()
    return render(request, 'subscription.html', {'subscription_plans': subscription_plans})


def configure_subscription(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_address = request.POST.get('customer_address', '').strip()
        delivery_days = request.POST.get('delivery_days', '')
        delivery_time = request.POST.get('delivery_time', '')
        diet_preference = request.POST.get('diet_preference', '')
        notes = request.POST.get('notes', '').strip()
        agree = request.POST.get('agree')

        if not (customer_name and customer_email and customer_phone and customer_address and delivery_days and delivery_time and agree):
            messages.error(request, '❌ Mohon lengkapi semua data wajib dan setujui syarat & ketentuan.')
        else:
            from urllib.parse import urlencode
            from django.urls import reverse
            
            schedule_str = f"{delivery_days} | {delivery_time}"
            params = {
                'subscription': plan.id,
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'customer_address': customer_address,
                'schedule': schedule_str,
                'diet': diet_preference,
                'notes': notes,
            }
            url = f"{reverse('checkout')}?{urlencode(params)}"
            return redirect(url)

    context = {
        'plan': plan,
        'delivery_days_options': [
            'Senin, Rabu, Jumat',
            'Selasa, Kamis, Sabtu',
            'Setiap Hari (Senin - Sabtu)'
        ],
        'delivery_time_options': [
            'Pagi (07:00 - 10:00)',
            'Siang (11:00 - 14:00)',
            'Sore (16:00 - 19:00)'
        ],
        'diet_options': [
            'Standar (Semua Makanan)',
            'Vegetarian',
            'Rendah Karbohidrat (Low Carb / Keto)',
            'Halal Premium',
            'Bebas Gluten (Gluten-Free)'
        ]
    }
    return render(request, 'subscription_configure.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})


def menu(request):
    category_slug = request.GET.get('category', '')
    search_query = request.GET.get('q', '')
    portion_filter = request.GET.get('portion', '')

    products = Product.objects.filter(is_available=True)

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search_query:
        products = products.filter(name__icontains=search_query)
    if portion_filter:
        products = products.filter(portion=portion_filter)

    categories = Category.objects.all()
    bundles = Bundle.objects.filter(is_active=True)
    addons = Addon.objects.filter(is_active=True)

    context = {
        'products': products,
        'categories': categories,
        'bundles': bundles,
        'addons': addons,
        'selected_category': category_slug,
        'search_query': search_query,
        'portion_filter': portion_filter,
    }
    return render(request, 'menu.html', context)


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        form = PartnershipForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Pesan Anda berhasil dikirim! Kami akan segera menghubungi Anda.')
            return redirect('contact')
    else:
        form = PartnershipForm()

    context = {'form': form}
    return render(request, 'contact.html', context)


def checkout(request):
    product_id = request.GET.get('product')
    subscription_id = request.GET.get('subscription')
    bundle_id = request.GET.get('bundle')

    product = None
    subscription = None
    bundle = None

    if product_id:
        product = get_object_or_404(Product, id=product_id)
    if subscription_id:
        subscription = get_object_or_404(SubscriptionPlan, id=subscription_id)
    if bundle_id:
        bundle = get_object_or_404(Bundle, id=bundle_id)

    addons = Addon.objects.filter(is_active=True)
    

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)

            # Hitung total harga
            base_price = 0
            if product:
                order.product = product
                base_price = int(product.price) * int(form.cleaned_data.get('quantity', 1) or 1)
            elif subscription:
                order.subscription = subscription
                base_price = int(subscription.price)
                order.subscription_schedule = request.POST.get('subscription_schedule', '')
                order.subscription_diet = request.POST.get('subscription_diet', '')

            elif bundle:
                order.bundle = bundle
                base_price = int(bundle.bundle_price) * int(form.cleaned_data.get('quantity', 1) or 1)

            # Cek referral code
            referral_code = form.cleaned_data.get('referral_code', '')
            discount = 0
            if referral_code:
                try:
                    ref = ReferralCode.objects.get(code=referral_code.upper(), is_active=True)
                    discount = base_price * ref.discount_percent / 100
                    ref.used_count += 1
                    ref.save()
                    order.referral_code = referral_code.upper()
                except ReferralCode.DoesNotExist:
                    pass

            # Hitung addon
            addon_ids = request.POST.getlist('addons')
            addon_total = 0
            if addon_ids:
                selected_addons = Addon.objects.filter(id__in=addon_ids)
                addon_total = sum(int(a.price) for a in selected_addons)

            order.total_price = max(0, base_price + addon_total - discount)
            order.save()

            if addon_ids:
                order.addons.set(Addon.objects.filter(id__in=addon_ids))

            messages.success(
                request,
                f'✅ Pesanan berhasil dibuat! Kode pesananmu: {order.order_code}'
            )
            # Tambahkan order ini ke order tracking session
            order_ids = request.session.get('my_order_ids', [])
            if order.id not in order_ids:
                order_ids.append(order.id)
                request.session['my_order_ids'] = order_ids
            
            order_statuses = request.session.get('order_statuses', {})
            order_statuses[str(order.id)] = order.status
            request.session['order_statuses'] = order_statuses
            
            # Tambah notifikasi awal
            notifications = request.session.get('notifications', [])
            new_notif = {
                'order_id': order.id,
                'order_code': order.order_code,
                'title': '📝 Pesanan Dibuat',
                'message': f'Pesanan {order.order_code} berhasil dibuat! Silakan tunggu konfirmasi pembayaran.',
                'status': order.status,
                'time': timezone.now().strftime('%H:%M'),
                'unread': True,
                'link': f'/order/{order.id}/'
            }
            notifications.insert(0, new_notif)
            request.session['notifications'] = notifications
            request.session.modified = True
            
            return redirect('order_success', order_id=order.id)
    else:
        initial_data = {}
        if request.GET.get('quantity'):
            initial_data['quantity'] = request.GET.get('quantity')
        form = OrderForm(initial=initial_data)

    preselected_addons = []
    addons_param = request.GET.get('addons', '')
    if addons_param:
        preselected_addons = [int(x) for x in addons_param.split(',') if x.isdigit()]

    context = {
        'form': form,
        'product': product,
        'subscription': subscription,
        'bundle': bundle,
        'addons': addons,
        'preselected_addons': preselected_addons,
    }
    return render(request, 'checkout.html', context)


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'success.html', {'order': order})


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_detail.html', {'order': order})


def track_order(request):
    """Halaman lacak pesanan by order_code"""
    order = None
    error = None
    code_input = ''

    if request.method == 'POST':
        code_input = request.POST.get('order_code', '').upper().strip()
        if code_input:
            try:
                order = Order.objects.get(order_code=code_input)
            except Order.DoesNotExist:
                error = f'Kode pesanan "{code_input}" tidak ditemukan. Periksa kembali kode pesananmu.'
        else:
            error = 'Masukkan kode pesanan terlebih dahulu.'
    elif request.GET.get('code'):
        code_input = request.GET.get('code', '').upper().strip()
        try:
            order = Order.objects.get(order_code=code_input)
        except Order.DoesNotExist:
            error = f'Kode pesanan "{code_input}" tidak ditemukan.'

    return render(request, 'track_order.html', {
        'order': order,
        'error': error,
        'code_input': code_input,
    })


def validate_coupon(request):
    code = request.GET.get('code', '').upper().strip()
    if not code:
        return JsonResponse({'valid': False, 'message': 'Kode promo kosong.'})
    
    # Check database
    try:
        ref = ReferralCode.objects.get(code=code, is_active=True)
        return JsonResponse({
            'valid': True,
            'discount_percent': ref.discount_percent,
            'free_shipping': False,
            'message': f'Kode promo "{code}" aktif! Diskon {ref.discount_percent}%.'
        })
    except ReferralCode.DoesNotExist:
        # Fallback for standard ones
        if code == 'HEMAT10':
            return JsonResponse({
                'valid': True,
                'discount_percent': 10,
                'free_shipping': False,
                'message': 'Promo HEMAT10 aktif! Diskon 10%.'
            })
        elif code == 'FREEONGKIR':
            return JsonResponse({
                'valid': True,
                'discount_percent': 0,
                'free_shipping': True,
                'message': 'Promo FREEONGKIR aktif! Gratis ongkir.'
            })
        return JsonResponse({
            'valid': False,
            'message': 'Kode promo tidak valid atau tidak aktif.'
        })


def mark_notifications_read(request):
    notifications = request.session.get('notifications', [])
    for notif in notifications:
        notif['unread'] = False
    request.session['notifications'] = notifications
    request.session.modified = True
    return JsonResponse({'status': 'ok'})