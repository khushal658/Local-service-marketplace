from .models import AdminNotification

def admin_navbar_notifications(request):
    try:
        notifications = AdminNotification.objects.order_by('-created_at')
        unread_count = notifications.filter(is_read=False).count()
        return {
            'admin_notifications': notifications[:6],
            'admin_unread_count': unread_count
        }
    except Exception:
        return {
            'admin_notifications': [],
            'admin_unread_count': 0
        }
