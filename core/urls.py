# core/urls.py
from django.urls import path
from . import views
from .views import register_view, login_view, logout_view

urlpatterns = [
    # Halaman utama
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('subscription/', views.subscription, name='subscription'),
    path('subscription/configure/<int:plan_id>/', views.configure_subscription, name='configure_subscription'),

    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Produk
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Checkout & Order
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('track/', views.track_order, name='track_order'),   # Bug #4 FIX: URL track_order ditambahkan

    # API / AJAX
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
    path('mark-notifications-read/', views.mark_notifications_read, name='mark_notifications_read'),

    # Auth
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
]
