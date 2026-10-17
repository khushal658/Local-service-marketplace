from user import models as us

def user_session_context(request):
    customer_id = request.session.get("customer_id")
    customer_photo = request.session.get("customer_photo")
    customer_name = request.session.get("customer_name")
    
    customer_unread_count = 0
    customer_notifications = []

    if customer_id:
        if not customer_photo:
            c = us.CustomerRegistration.objects.filter(id=customer_id).first()
            if c:
                if c.profile_photo:
                    customer_photo = c.profile_photo.url
                else:
                    name_str = c.full_name or customer_name or "User"
                    customer_photo = f"https://ui-avatars.com/api/?name={name_str.replace(' ', '+')}&background=ffffff&color=047857&bold=true&rounded=true"
                request.session["customer_photo"] = customer_photo

        try:
            from customer.models import CustomerNotification
            notifs = CustomerNotification.objects.filter(customer_id=customer_id).order_by('-created_at')
            customer_unread_count = notifs.filter(is_read=False).count()
            customer_notifications = notifs[:8]
        except Exception:
            pass

    provider_id = request.session.get("provider_id")
    provider_photo = request.session.get("provider_photo")
    provider_name = request.session.get("provider_name")
    
    if provider_id:
        if not provider_photo:
            p = us.ServiceProvider.objects.filter(id=provider_id).first()
            if p:
                if p.profile_image:
                    provider_photo = p.profile_image.url
                else:
                    name_str = p.full_name or provider_name or "Provider"
                    provider_photo = f"https://ui-avatars.com/api/?name={name_str.replace(' ', '+')}&background=ffffff&color=092b23&bold=true&rounded=true"
                request.session["provider_photo"] = provider_photo

    return {
        'customer_photo': customer_photo,
        'provider_photo': provider_photo,
        'customer_unread_count': customer_unread_count,
        'customer_notifications': customer_notifications,
    }
