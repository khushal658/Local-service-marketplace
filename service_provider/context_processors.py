from user.models import ServiceProvider
from .models import ProviderNotification

def provider_navbar_notifications(request):
    provider_id = request.session.get("provider_id")
    if provider_id:
        try:
            provider = ServiceProvider.objects.get(id=provider_id)
            notifications = ProviderNotification.objects.filter(provider=provider).order_by('-created_at')
            unread_count = notifications.filter(is_read=False).count()
            return {
                'navbar_notifications': notifications[:6],
                'navbar_unread_count': unread_count
            }
        except Exception:
            pass
    return {
        'navbar_notifications': [],
        'navbar_unread_count': 0
    }
