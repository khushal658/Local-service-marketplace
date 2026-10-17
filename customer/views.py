from django.shortcuts import render,redirect,get_object_or_404
from user import models as us  # तुमचे CustomerRegistration मॉडेल जिथे आहे ते ॲप
from django.contrib import messages
from . import models as cm 
from adminpanel import models as ad


from django.conf import settings
from django.http import JsonResponse

try:
    import razorpay
    razorpay_client = razorpay.Client(auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', '')))
except ImportError:
    razorpay = None
    razorpay_client = None
# from .models import ServiceQuote, CustomServiceRequest


# Create your views here.

def customer_dashboard(request):
    return redirect('user_index')

def customer_logout(request):
    request.session.flush()
    if request.user.is_authenticated:
        from django.contrib.auth import logout as django_logout
        django_logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('user_index')




def customer_profile(request):
    # 1. Login Check (सेशन किंवा Auth यूजर तपासा)
    customer_id = request.session.get("customer_id")
    customer = None

    if customer_id:
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    elif request.user.is_authenticated:
        customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()

    if not customer:
        messages.error(request, "Please log in to view your profile.")
        return redirect('login')

    # 2. Form Update (POST Request)
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        gender = request.POST.get('gender', '').strip()
        dob = request.POST.get('dob', '').strip() or None
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        profile_photo = request.FILES.get('profile_photo')

        # Mobile Duplicate Validation (स्वतःचा नंबर सोडून इतर कोणाचा नाही ना हे तपासणे)
        if mobile and us.CustomerRegistration.objects.filter(mobile=mobile).exclude(id=customer.id).exists():
            messages.error(request, "This mobile number is already used by another account.")
            return render(request, 'customer/profile.html', {'customer': customer})

        # Data Updating
        customer.full_name = full_name
        customer.mobile = mobile
        customer.gender = gender if gender else None
        customer.dob = dob
        customer.address = address
        customer.city = city
        customer.state = state
        customer.pincode = pincode

        if profile_photo:
            customer.profile_photo = profile_photo

        customer.save()

        # Update Session Name & Photo
        request.session["customer_name"] = customer.full_name
        request.session["customer_photo"] = customer.profile_photo.url if customer.profile_photo else None

        messages.success(request, "Your profile has been updated successfully!")
        return redirect('customer_profile')

    # 3. Load Profile Page (GET Request)
    if customer and customer.profile_photo:
        request.session["customer_photo"] = customer.profile_photo.url
    return render(request, 'customer/profile.html', {'customer': customer})


from django.http import JsonResponse
from .models import CustomServiceRequest

def post_custom_request(request):
    if request.method == 'POST':
        customer_id = request.session.get("customer_id")
        customer = None
        if customer_id:
            customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
        elif request.user.is_authenticated:
            customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                       us.CustomerRegistration.objects.filter(email=request.user.email).first()

        if not customer:
            return JsonResponse({'success': False, 'message': 'Please log in as a customer to post a custom request.'})

        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', '').strip()
        description = request.POST.get('description', '').strip()
        city_area = request.POST.get('city_area', '').strip()
        budget = request.POST.get('budget', '').strip()
        preferred_date_str = request.POST.get('preferred_date', '').strip()

        if not title or not description or not city_area:
            return JsonResponse({'success': False, 'message': 'Please fill in Title, Description, and City/Area.'})

        preferred_date = None
        if preferred_date_str:
            try:
                from datetime import datetime, date
                parsed_date = datetime.strptime(preferred_date_str, '%Y-%m-%d').date()
                if parsed_date < date.today():
                    return JsonResponse({'success': False, 'message': 'Preferred date cannot be in the past. Please select today or a future date.'})
                preferred_date = parsed_date
            except ValueError:
                pass

        CustomServiceRequest.objects.create(
            customer=customer,
            title=title,
            category=category,
            description=description,
            city_area=city_area,
            budget=budget,
            preferred_date=preferred_date,
            status='pending'
        )

        return JsonResponse({
            'success': True, 
            'message': 'Your custom service request has been posted successfully! Nearby service providers will view it soon.'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def customer_direct_bookings(request):
    """ग्राहकाने थेट बुक केलेल्या सर्व्हिस बुकिंग्ज दाखवणारा व्ह्यू (Filter Buttons + Pagination सह)"""
    customer_id = request.session.get("customer_id")
    customer = None
    if customer_id:
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    elif request.user.is_authenticated:
        customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()

    if not customer:
        messages.error(request, "Please log in to view your direct bookings.")
        return redirect('login')

    status_filter = request.GET.get('status', 'all').strip().lower()

    all_bookings = us.DirectServiceBooking.objects.filter(customer=customer).order_by('-created_at')

    # Counts for Filter Badges
    total_count = all_bookings.count()
    pending_count = all_bookings.filter(status='pending').count()
    accepted_count = all_bookings.filter(status='accepted').count()
    rejected_count = all_bookings.filter(status='cancelled').count()
    completed_count = all_bookings.filter(status='completed').count()

    # Filter by Status
    if status_filter in ['approved', 'accepted']:
        bookings_list = all_bookings.filter(status='accepted')
        status_filter = 'approved'
    elif status_filter == 'pending':
        bookings_list = all_bookings.filter(status='pending')
    elif status_filter in ['rejected', 'cancelled']:
        bookings_list = all_bookings.filter(status='cancelled')
        status_filter = 'rejected'
    elif status_filter == 'completed':
        bookings_list = all_bookings.filter(status='completed')
    else:
        status_filter = 'all'
        bookings_list = all_bookings

    # Pagination: 6 direct bookings per page
    from django.core.paginator import Paginator
    paginator = Paginator(bookings_list, 6)
    page_number = request.GET.get('page')
    direct_bookings = paginator.get_page(page_number)

    for booking in direct_bookings:
        provider = us.ServiceProvider.objects.filter(email=booking.provider_email).first()
        booking.provider_info = provider

    notifications = cm.CustomerNotification.objects.filter(customer=customer).order_by('-created_at')
    unread_notif_count = notifications.filter(is_read=False).count()

    context = {
        'customer': customer,
        'direct_bookings': direct_bookings,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'completed_count': completed_count,
        'notifications': notifications,
        'unread_notif_count': unread_notif_count
    }
    return render(request, 'customer/direct_bookings.html', context)


def my_requests(request):
    """ग्राहकाने पोस्ट केलेल्या कस्टम मागण्या दाखवणारा व्ह्यू"""
    customer_id = request.session.get("customer_id")
    customer = None
    if customer_id:
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    elif request.user.is_authenticated:
        customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()

    if not customer:
        messages.error(request, "Please log in to view your service requests.")
        return redirect('login')

    requests_list = CustomServiceRequest.objects.filter(customer=customer).order_by('-created_at')

    # Pagination: 12 cards per page
    from django.core.paginator import Paginator
    paginator = Paginator(requests_list, 12)
    page_number = request.GET.get('page')
    custom_requests = paginator.get_page(page_number)

    categories = ad.Category.objects.filter(is_active=True)
    notifications = cm.CustomerNotification.objects.filter(customer=customer).order_by('-created_at')
    unread_notif_count = notifications.filter(is_read=False).count()

    context = {
        'customer': customer,
        'custom_requests': custom_requests,
        'categories': categories,
        'notifications': notifications,
        'unread_notif_count': unread_notif_count
    }
    return render(request, 'customer/my_requests.html', context)


def accept_quote(request, quote_id):
    customer_id = request.session.get("customer_id")
    customer = None
    if customer_id:
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    elif request.user.is_authenticated:
        customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()

    if not customer:
        messages.error(request, "Please log in first.")
        return redirect('login')

    quote = get_object_or_404(cm.ServiceQuote, id=quote_id, request__customer=customer)
    
    # 1. Update quote status to accepted
    quote.status = 'accepted'
    quote.save()

    # 2. Update request status to accepted
    custom_req = quote.request
    custom_req.status = 'accepted'
    custom_req.save()

    # 3. Reject other quotes for this request
    cm.ServiceQuote.objects.filter(request=custom_req).exclude(id=quote.id).update(status='rejected')

    # 4. Create Notification for Service Provider
    try:
        from service_provider.models import ProviderNotification
        ProviderNotification.objects.create(
            provider=quote.provider,
            title="Offer Accepted by Customer!",
            message=f"Customer {customer.full_name} accepted your quote of ₹{quote.quoted_price} for '{custom_req.title}'. Customer Mobile: {customer.mobile}, Location: {custom_req.city_area}."
        )
    except Exception as e:
        print("Notification error:", e)

    messages.success(request, f"You accepted the quote of ₹{quote.quoted_price} from {quote.provider.full_name}!")
    return redirect('customer_my_requests')


def delete_custom_request(request, request_id):
    customer_id = request.session.get("customer_id")
    customer = None
    if customer_id:
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    elif request.user.is_authenticated:
        customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()

    if not customer:
        messages.error(request, "Please log in first.")
        return redirect('login')

    custom_req = get_object_or_404(CustomServiceRequest, id=request_id, customer=customer)
    custom_req.delete()

    messages.success(request, "Your service request has been deleted successfully.")
    return redirect('customer_my_requests')


def edit_custom_request(request, request_id):
    customer_id = request.session.get("customer_id")
    customer = None
    if customer_id:
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    elif request.user.is_authenticated:
        customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()

    if not customer:
        return JsonResponse({'success': False, 'message': 'Please log in first.'})

    custom_req = get_object_or_404(cm.CustomServiceRequest, id=request_id, customer=customer)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', '').strip()
        description = request.POST.get('description', '').strip()
        city_area = request.POST.get('city_area', '').strip()
        budget = request.POST.get('budget', '').strip()
        preferred_date_str = request.POST.get('preferred_date', '').strip()

        if not title or not description or not city_area:
            return JsonResponse({'success': False, 'message': 'Title, Description and City/Area are required.'})

        preferred_date = None
        if preferred_date_str:
            try:
                from datetime import datetime, date
                parsed_date = datetime.strptime(preferred_date_str, '%Y-%m-%d').date()
                if parsed_date < date.today():
                    return JsonResponse({'success': False, 'message': 'Preferred date cannot be in the past.'})
                preferred_date = parsed_date
            except ValueError:
                pass

        custom_req.title = title
        custom_req.category = category
        custom_req.description = description
        custom_req.city_area = city_area
        custom_req.budget = budget
        custom_req.preferred_date = preferred_date
        custom_req.save()

        return JsonResponse({'success': True, 'message': 'Your custom request has been updated successfully.'})

    return JsonResponse({
        'success': True,
        'data': {
            'id': custom_req.id,
            'title': custom_req.title,
            'category': custom_req.category or '',
            'description': custom_req.description,
            'city_area': custom_req.city_area,
            'budget': custom_req.budget or '',
            'preferred_date': custom_req.preferred_date.strftime('%Y-%m-%d') if custom_req.preferred_date else ''
        }
    })






def create_razorpay_order(request, quote_id):
    """१. Razorpay Order ID तयार करणे"""
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return JsonResponse({'success': False, 'message': 'Please log in first.'})

    if not razorpay_client:
        return JsonResponse({'success': False, 'message': 'Razorpay library is not installed on server.'})

    quote = get_object_or_404(cm.ServiceQuote, id=quote_id, request__customer__id=customer_id)
    
    amount_to_pay = quote.final_amount if quote.final_amount else quote.quoted_price
    amount_in_paise = int(float(amount_to_pay) * 100) # रक्कमेची गणना पैशांमध्ये

    # Razorpay Order Create
    razorpay_order = razorpay_client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    quote.razorpay_order_id = razorpay_order['id']
    quote.payment_mode = 'online'
    quote.save()

    return JsonResponse({
        'success': True,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'order_id': razorpay_order['id'],
        'amount': amount_in_paise,
        'customer_name': quote.request.customer.full_name,
        'customer_email': quote.request.customer.email,
        'customer_mobile': quote.request.customer.mobile,
        'quote_id': quote.id
    })


def verify_razorpay_payment(request):
    """२. ऑनलाईन पेमेंट (QR Code/UPI/Card) झाल्यावर Signature तपासणे व extra_tags सह मेसेज पाठवणे"""
    if request.method == "POST":
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        quote_id = request.POST.get('quote_id')

        quote = get_object_or_404(cm.ServiceQuote, id=quote_id)

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # १. पेमेंट यशस्वी -> डेटाबेस अपडेट करणे
            quote.payment_status = 'paid'
            quote.payment_mode = 'online'
            quote.razorpay_payment_id = razorpay_payment_id
            quote.razorpay_signature = razorpay_signature
            
            # २. मूळ सर्व्हिस मागणी Completed करणे
            quote.request.status = 'completed'
            quote.request.save()
            quote.save()

            # ३. ॲडमिनला 10% Commission Notification पाठवणे
            try:
                from adminpanel.models import AdminNotification
                from service_provider.models import ProviderNotification
                final_amt = float(quote.final_amount) if quote.final_amount else float(quote.quoted_price)
                admin_share = round(final_amt * 0.10, 2)
                
                # Admin Notification
                AdminNotification.objects.create(
                    title=f"🎉 10% Commission Received! (+₹{admin_share:.2f})",
                    message=f"Customer '{quote.request.customer.full_name}' paid ₹{final_amt:.2f} for '{quote.request.title}' via Online Payment. Admin 10% Share: ₹{admin_share:.2f}."
                )

                # Provider Notification
                ProviderNotification.objects.create(
                    provider=quote.provider,
                    title=f"💰 Online Payment Received: ₹{final_amt:.2f}!",
                    message=f"Customer '{quote.request.customer.full_name}' paid ₹{final_amt:.2f} online for '{quote.request.title}' via Razorpay (ID: {razorpay_payment_id})."
                )

                # Customer Notification
                cm.CustomerNotification.objects.create(
                    customer=quote.request.customer,
                    title="Online Payment Successful! 💳",
                    message=f"Your online payment of ₹{final_amt:.2f} for '{quote.request.title}' was successful via Razorpay (ID: {razorpay_payment_id})."
                )
            except Exception as e:
                print("Payment Notification error:", e)

            # ४. extra_tags सह Success Message
            messages.success(request, "🎉 Payment Successful! Your service booking is completed.", extra_tags="payment_msg")
            return JsonResponse({'success': True, 'message': 'Payment successful!'})

        except razorpay.errors.SignatureVerificationError:
            # ४. extra_tags सह Error Message
            messages.error(request, "⚠️ Payment Verification Failed! Please try again.", extra_tags="payment_msg")
            return JsonResponse({'success': False, 'message': 'Payment verification failed!'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})


def pay_cash(request, quote_id):
    """३. ग्राहकाने Cash Payment निवडल्यावर पेमेंट सेव्ह करणे"""
    customer_id = request.session.get("customer_id")
    customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    if not customer:
        messages.error(request, "Please log in first.")
        return redirect('login')

    quote = get_object_or_404(cm.ServiceQuote, id=quote_id, request__customer=customer)

    quote.payment_mode = 'cash'
    quote.payment_status = 'paid'
    quote.status = 'completed'
    quote.save()

    custom_req = quote.request
    custom_req.status = 'completed'
    custom_req.save()

    # Notify Provider & Admin & Customer
    try:
        from service_provider.models import ProviderNotification
        from adminpanel.models import AdminNotification
        final_amt = quote.final_amount if quote.final_amount else quote.quoted_price
        admin_share = round(float(final_amt) * 0.10, 2)
        
        ProviderNotification.objects.create(
            provider=quote.provider,
            title=f"Cash Payment Confirmed: ₹{final_amt}!",
            message=f"Customer {customer.full_name} marked Cash Payment as paid for '{custom_req.title}'. Amount: ₹{final_amt}."
        )

        AdminNotification.objects.create(
            title=f"🎉 10% Commission Received! (+₹{admin_share:.2f})",
            message=f"Customer '{customer.full_name}' paid ₹{final_amt} for '{custom_req.title}' via Cash Payment. Admin 10% Share: ₹{admin_share:.2f}."
        )

        cm.CustomerNotification.objects.create(
            customer=customer,
            title="Cash Payment Recorded! 💵",
            message=f"Your cash payment of ₹{final_amt} for '{custom_req.title}' was recorded for provider {quote.provider.full_name}."
        )
    except Exception as e:
        print("Notification error:", e)

    messages.success(request, f"Cash Payment confirmed! Please leave a review for {quote.provider.full_name}.", extra_tags="payment_msg")
    return redirect('customer_my_requests')


def submit_provider_review(request, quote_id):
    """४. काम व पेमेंट पूर्ण झाल्यावर ग्राहकाने प्रोव्हायडरला Rating & Review देणे"""
    if request.method == 'POST':
        customer_id = request.session.get("customer_id")
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
        if not customer:
            messages.error(request, "Please log in first.")
            return redirect('login')

        quote = get_object_or_404(cm.ServiceQuote, id=quote_id, request__customer=customer)
        rating_str = request.POST.get('rating', '5')
        review_text = request.POST.get('review_text', '').strip()

        try:
            rating = int(rating_str)
        except ValueError:
            rating = 5

        # ProviderReview Create or Update
        cm.ProviderReview.objects.update_or_create(
            provider=quote.provider,
            customer=customer,
            request=quote.request,
            defaults={
                'rating': rating,
                'review_text': review_text
            }
        )

        # Notify Service Provider about the new Review & Rating
        try:
            from service_provider.models import ProviderNotification
            stars = "★" * rating
            ProviderNotification.objects.create(
                provider=quote.provider,
                title=f"⭐ New {rating}-Star Review Received!",
                message=f"Customer '{customer.full_name}' gave you a {rating}-star rating ({stars}) for '{quote.request.title}': \"{review_text}\""
            )
        except Exception as e:
            print("Provider Review Notification error:", e)

        messages.success(request, f"Thank you! Your review for {quote.provider.full_name} has been submitted.", extra_tags="customer_req")
        return redirect('customer_my_requests')
    return redirect('customer_my_requests')


def customer_payments(request):
    """५. ग्राहकाचे Payments & Wallet आणि Transaction History (२० प्रति पान)"""
    customer_id = request.session.get("customer_id")
    customer = None
    if customer_id:
        customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
    elif request.user.is_authenticated:
        customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()

    if not customer:
        messages.error(request, "Please log in first.")
        return redirect('login')

    paid_quotes = cm.ServiceQuote.objects.filter(
        request__customer=customer,
        payment_status='paid'
    ).order_by('-created_at')

    total_spent = 0.0
    online_spent = 0.0
    cash_spent = 0.0

    for q in paid_quotes:
        amt = float(q.final_amount) if q.final_amount else float(q.quoted_price)
        total_spent += amt
        if q.payment_mode == 'online':
            online_spent += amt
        else:
            cash_spent += amt

    total_orders = paid_quotes.count()

    # Pagination: 20 transactions per page
    from django.core.paginator import Paginator
    paginator = Paginator(paid_quotes, 20)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    notifications = cm.CustomerNotification.objects.filter(customer=customer).order_by('-created_at')
    unread_notif_count = notifications.filter(is_read=False).count()

    context = {
        'customer': customer,
        'total_spent': total_spent,
        'online_spent': online_spent,
        'cash_spent': cash_spent,
        'total_orders': total_orders,
        'transactions': transactions,
        'notifications': notifications,
        'unread_notif_count': unread_notif_count
    }
    return render(request, 'customer/payments.html', context)


def download_receipt(request, quote_id):
    """६. पेमेंट पावती / Payment Tax Invoice Download & Print View"""
    customer_id = request.session.get("customer_id")
    provider_id = request.session.get("provider_id")

    quote = get_object_or_404(cm.ServiceQuote, id=quote_id, payment_status='paid')

    is_customer = customer_id and quote.request.customer.id == customer_id
    is_provider = provider_id and quote.provider.id == provider_id

    if not is_customer and not is_provider:
        if request.user.is_authenticated:
            if request.user.email == quote.request.customer.email or request.user.email == quote.provider.email or request.user.is_staff:
                pass
            else:
                messages.error(request, "Unauthorized access to receipt.")
                return redirect('home')
        else:
            messages.error(request, "Please log in to view this receipt.")
            return redirect('login')

    final_amt = quote.final_amount if quote.final_amount else quote.quoted_price

    context = {
        'quote': quote,
        'final_amount': final_amt,
    }
    return render(request, 'common/payment_receipt.html', context)


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def mark_customer_notifications_read(request):
    """Notification bell click केल्यावर सर्व Unread Customer Notifications Read करणे"""
    customer_id = request.session.get("customer_id")
    if not customer_id and request.user.is_authenticated:
        c = us.CustomerRegistration.objects.filter(user=request.user).first() or \
            us.CustomerRegistration.objects.filter(email=request.user.email).first()
        if c:
            customer_id = c.id

    if customer_id:
        cm.CustomerNotification.objects.filter(customer_id=customer_id, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)
