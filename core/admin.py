

# Register your models here.
from django.contrib import admin
from .models import (
    Category, Product, Addon, SubscriptionPlan,
    Bundle, LoyaltyTier, Order, ReferralCode,
    SeasonalCampaign, Partnership, ProductImage
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'portion', 'price', 'is_featured', 'is_available']
    list_filter = ['category', 'portion', 'is_featured', 'is_available']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'total_price', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['customer_name', 'customer_email']
    list_editable = ['status']


@admin.register(SubscriptionPlan)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration', 'price', 'is_popular']


@admin.register(SeasonalCampaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_percent', 'start_date', 'end_date', 'is_active']


@admin.register(ReferralCode)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'used_count', 'is_active']


admin.site.register(Addon)
admin.site.register(Bundle)
admin.site.register(LoyaltyTier)
admin.site.register(Partnership)


admin.site.site_header = "🍽️ Meal N Home Admin"
admin.site.site_title = "Meal N Home"
admin.site.index_title = "Dashboard Admin"