from .models import Order
from django.utils import timezone

def notifications_processor(request):
    # Inisialisasi session jika belum ada
    if 'notifications' not in request.session:
        request.session['notifications'] = []
    if 'my_order_ids' not in request.session:
        request.session['my_order_ids'] = []
    if 'order_statuses' not in request.session:
        request.session['order_statuses'] = {}

    my_order_ids = request.session.get('my_order_ids', [])
    order_statuses = request.session.get('order_statuses', {})
    notifications = request.session.get('notifications', [])

    # Sinkronisasi status pesanan dari database
    if my_order_ids:
        # Ambil order terbaru dari database
        db_orders = Order.objects.filter(id__in=my_order_ids)
        status_changed = False

        for order in db_orders:
            str_id = str(order.id)
            current_status = order.status
            previous_status = order_statuses.get(str_id)

            # Jika ini order baru yang belum dicatat, atau statusnya berubah
            if previous_status is None:
                # Catat status awal
                order_statuses[str_id] = current_status
                status_changed = True
            elif previous_status != current_status:
                # Status berubah! Buat notifikasi baru
                status_label = order.get_status_display()
                
                # Desain pesan yang menarik sesuai status
                emoji = '⏳'
                if current_status == 'paid':
                    emoji = '💳'
                    msg = f'Pembayaran diterima! Pesanan {order.order_code} siap diproses.'
                elif current_status == 'processing':
                    emoji = '👨‍🍳'
                    msg = f'Pesanan {order.order_code} sedang disiapkan oleh chef kami.'
                elif current_status == 'delivered':
                    emoji = '🚚'
                    msg = f'Pesanan {order.order_code} sedang dalam pengiriman ke alamatmu!'
                elif current_status == 'completed':
                    emoji = '🏠'
                    msg = f'Pesanan {order.order_code} telah selesai dan sampai tujuan. Selamat menikmati!'
                elif current_status == 'cancelled':
                    emoji = '❌'
                    msg = f'Pesanan {order.order_code} telah dibatalkan.'
                else:
                    msg = f'Status pesanan {order.order_code} berubah menjadi {status_label}.'

                new_notif = {
                    'order_id': order.id,
                    'order_code': order.order_code,
                    'title': f'{emoji} Status Update',
                    'message': msg,
                    'status': current_status,
                    'time': timezone.now().strftime('%H:%M'),
                    'unread': True,
                    'link': f'/order/{order.id}/'
                }
                
                # Masukkan ke list teratas
                notifications.insert(0, new_notif)
                order_statuses[str_id] = current_status
                status_changed = True

        if status_changed:
            request.session['order_statuses'] = order_statuses
            request.session['notifications'] = notifications
            # Tandai session dimodifikasi agar Django menyimpannya
            request.session.modified = True

    # Hitung jumlah notifikasi yang belum dibaca
    unread_count = sum(1 for n in notifications if n.get('unread', False))

    return {
        'user_notifications': notifications[:10], # batasi 10 terakhir di dropdown
        'unread_notifications_count': unread_count
    }
