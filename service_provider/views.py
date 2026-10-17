from django.shortcuts import render,redirect,get_object_or_404
from user import models as us
from django.contrib import messages 
from adminpanel import models as ad
from . import models as sr
import os
import uuid
from django.http import JsonResponse


# Create your views here.

def provider_dashboard(request):

    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")

    try:
        provider = us.ServiceProvider.objects.get(
            id=provider_id
        )
    except us.ServiceProvider.DoesNotExist:

        request.session.flush()
        return redirect("login")

    from customer.models import ServiceQuote
    from .models import ProviderNotification

    accepted_jobs = ServiceQuote.objects.filter(provider=provider, status='accepted').order_by('-created_at')
    notifications = ProviderNotification.objects.filter(provider=provider).order_by('-created_at')
    unread_notif_count = notifications.filter(is_read=False).count()

    return render(
        request,
        "service_provider/index.html",
        {
            "provider": provider,
            "accepted_jobs": accepted_jobs,
            "notifications": notifications,
            "unread_notif_count": unread_notif_count
        }
    )


def provider_logout(request):
    request.session.flush()
    return redirect("login")

# update profile

def provider_profile_update(request):

    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")

    try:
        provider = us.ServiceProvider.objects.get(
            id=provider_id
        )

    except us.ServiceProvider.DoesNotExist:
        request.session.flush()
        return redirect("login")

    if request.method == "POST":

        # --------------------------------
        # ONLY EDITABLE FIELDS
        # --------------------------------

        provider.full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        provider.business_name = request.POST.get(
            "business_name",
            ""
        ).strip()

        provider.mobile = request.POST.get(
            "mobile",
            ""
        ).strip()

        provider.city_area = request.POST.get(
            "city_area",
            ""
        ).strip()

        provider.pincode = request.POST.get(
            "pincode",
            ""
        ).strip()

        provider.experience = request.POST.get(
            "experience",
            ""
        ).strip()

        # if request.FILES.get("profile_image"):

        #     provider.profile_image = request.FILES.get(
        #         "profile_image"
        #     )
       

        if request.method == "POST":

            profile_image = request.FILES.get("profile_image")

            if profile_image:
                provider.profile_image = profile_image

            provider.save()
        messages.success(
            request,
            "Profile updated successfully!"
        )

        return redirect(
            "provider_profile_update"
        )

    return render(
        request,
        "service_provider/profile.html",
        {
            "provider": provider
        }
    )

# add new service 

def add_service(request):

    # प्रोव्हायडर लॉगिन आहे का ते पाहणे
    provider_id = request.session.get('provider_id')
    if not provider_id:
        messages.warning(request, "Please log in to add services.")
        return redirect('login')
    try:
        provider = us.ServiceProvider.objects.get(id=provider_id)
    except us.ServiceProvider.DoesNotExist:
        return redirect('login')
    if request.method == 'POST':
        service_name = request.POST.get('service_name', '').strip()
        category_id = request.POST.get('category_id')
        subcategory_id = request.POST.get('subcategory_id')
        service_description = request.POST.get('service_description', '').strip()
        price = request.POST.get('price', '0').strip() or '0'
        service_area = request.POST.get('service_area', '').strip()
        service_pincode = request.POST.get('service_pincode', '').strip()
        experience = request.POST.get('experience', '').strip()
        skills_included = request.POST.get('skills_included', '').strip()
        availability = request.POST.get('availability', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        service_image = request.FILES.get('service_image') # Main image
        gallery_image1 = request.FILES.get('gallery_image1')
        gallery_image2 = request.FILES.get('gallery_image2')
        gallery_image3 = request.FILES.get('gallery_image3')
        
        service_video = request.FILES.get('service_video') # Video 1
        service_video2 = request.FILES.get('service_video2') # Video 2

        # Helper function for Image validation (Max 2MB)
        def validate_image_file(img_file, file_label="Image"):
            if img_file:
                valid_img_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                ext = os.path.splitext(img_file.name)[1].lower()
                if ext not in valid_img_extensions or not img_file.content_type.startswith('image/'):
                    return f"Invalid format for {file_label}! Only (JPG, JPEG, PNG, WEBP) are allowed."
                if img_file.size > 2 * 1024 * 1024:
                    return f"{file_label} size must be less than 2 MB."
            return None

        # Helper function for Video validation (Max 10MB)
        def validate_video_file(vid_file, file_label="Video"):
            if vid_file:
                valid_vid_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.mkv']
                ext = os.path.splitext(vid_file.name)[1].lower()
                if ext not in valid_vid_extensions or not vid_file.content_type.startswith('video/'):
                    return f"Invalid format for {file_label}! Only (MP4, WEBM, OGG, MOV, MKV) are allowed."
                if vid_file.size > 10 * 1024 * 1024:
                    return f"{file_label} size must be less than 10 MB."
            return None

        # Check required media: At least 1 Gallery Photo and 1 Video are required
        if not gallery_image1:
            messages.error(request, "At least 1 Gallery Photo is required!")
            return redirect('add_service')

        if not service_video:
            messages.error(request, "At least 1 Promotional Video is required!")
            return redirect('add_service')

        # Validate images
        for img, lbl in [(service_image, "Main Cover Image"), (gallery_image1, "Gallery Image 1"), (gallery_image2, "Gallery Image 2"), (gallery_image3, "Gallery Image 3")]:
            err = validate_image_file(img, lbl)
            if err:
                messages.error(request, err)
                return redirect('add_service')

        # Validate videos
        for vid, lbl in [(service_video, "Video 1"), (service_video2, "Video 2")]:
            err = validate_video_file(vid, lbl)
            if err:
                messages.error(request, err)
                return redirect('add_service')

        # Available Days Extraction (Mon-Sun or All Days)
        selected_days = request.POST.getlist('available_days')
        if 'All Days' in selected_days or len(selected_days) == 7:
            available_days_str = "All Days (Mon - Sun)"
        elif selected_days:
            available_days_str = ", ".join(selected_days)
        else:
            available_days_str = request.POST.get('available_days_custom', '').strip() or "All Days (Mon - Sun)"

        try:
            category_obj = ad.Category.objects.get(id=category_id)
            subcategory_obj = ad.SubCategory.objects.get(id=subcategory_id) if subcategory_id else None
            sr.AddService.objects.create(
                provider_email=provider.email,
                service_name=service_name,
                category=category_obj,
                subcategory=subcategory_obj,
                service_description=service_description,
                service_image=service_image,
                gallery_image1=gallery_image1,
                gallery_image2=gallery_image2,
                gallery_image3=gallery_image3,
                service_video=service_video,
                service_video2=service_video2,
                price=price,
                service_area=service_area,
                service_pincode=service_pincode,
                experience=experience,
                skills_included=skills_included,
                availability=availability,
                available_days=available_days_str,
                contact_number=contact_number
            )
            messages.success(request, "New Service Posted Successfully! 🎉", extra_tags="service_added")
            return redirect('add_service')
        except Exception as e:
            print("ERROR SAVING SERVICE:", e)
            messages.error(request, "Failed to save service. Please try again.")
    # GET Request: Active Categories मिळवणे
    categories = ad.Category.objects.filter(is_active=True)
    subcategories = ad.SubCategory.objects.filter(is_active=True)
    context = {
        'provider': provider,
        'categories': categories,
        'subcategories': subcategories
    }
    return render(request, 'service_provider/add_service.html', context)


# fakta category chi subcategory choose sathi fun

def get_subcategories_by_category(request):
    cat_id = request.GET.get('category_id')
    if not cat_id:
        return JsonResponse({'subcategories': []})
    try:
        subcategories = list(ad.SubCategory.objects.filter(category_id=cat_id, is_active=True).values('id', 'subcat_names'))
        for sub in subcategories:
            sub['id'] = str(sub['id'])
        return JsonResponse({'subcategories': subcategories})
    except Exception as e:
        print("ERROR FETCHING SUBCATEGORIES:", e)
        return JsonResponse({'subcategories': []})


# service list
def my_services_list(request):
    provider_id = request.session.get('provider_id')
    if not provider_id:
        return redirect('login')
        
    try:
        provider = us.ServiceProvider.objects.get(id=provider_id)
    except us.ServiceProvider.DoesNotExist:
        return redirect('login')

    # लॉगिन असलेल्या प्रोव्हायडरच्या सर्व सर्व्हिसेस मिळवणे:
    services = sr.AddService.objects.filter(provider_email=provider.email).order_by('-created_at')

    context = {
        'provider': provider,
        'services': services,
        'total_services': services.count()
    }
    return render(request, 'service_provider/my_services.html', context)

# edit service

def edit_service(request, service_id):
    # १. लॉगिन सुरक्षा
    provider_id = request.session.get('provider_id')
    if not provider_id:
        messages.warning(request, "Please log in to edit services.")
        return redirect('login')

    try:
        provider = us.ServiceProvider.objects.get(id=provider_id)
    except us.ServiceProvider.DoesNotExist:
        return redirect('login')

    # २. सर्व्हिस ऑब्जेक्ट मिळवणे
    service = get_object_or_404(sr.AddService, id=service_id)

    if request.method == 'POST':
        service_name = request.POST.get('service_name', '').strip()
        category_id = request.POST.get('category_id')
        subcategory_id = request.POST.get('subcategory_id')
        price = request.POST.get('price', '0').strip()
        service_area = request.POST.get('service_area', '').strip()
        service_pincode = request.POST.get('service_pincode', '').strip()
        experience = request.POST.get('experience', '').strip()
        availability = request.POST.get('availability', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        skills_included = request.POST.get('skills_included', '').strip()
        service_description = request.POST.get('service_description', '').strip()
        
        new_image = request.FILES.get('service_image')
        new_g1 = request.FILES.get('gallery_image1')
        new_g2 = request.FILES.get('gallery_image2')
        new_g3 = request.FILES.get('gallery_image3')
        new_v1 = request.FILES.get('service_video')
        new_v2 = request.FILES.get('service_video2')

        # Helper function for Image validation
        def validate_img(img_file, file_label):
            if img_file:
                valid_exts = ['.jpg', '.jpeg', '.png', '.webp']
                ext = os.path.splitext(img_file.name)[1].lower()
                if ext not in valid_exts or not img_file.content_type.startswith('image/'):
                    return f"Invalid image format for {file_label}! Only (JPG, JPEG, PNG, WEBP) are allowed."
                if img_file.size > 2 * 1024 * 1024:
                    return f"{file_label} size must be less than 2 MB."
            return None

        # Helper function for Video validation
        def validate_vid(vid_file, file_label):
            if vid_file:
                valid_exts = ['.mp4', '.webm', '.ogg', '.mov', '.mkv']
                ext = os.path.splitext(vid_file.name)[1].lower()
                if ext not in valid_exts or not vid_file.content_type.startswith('video/'):
                    return f"Invalid video format for {file_label}! Only (MP4, WEBM, OGG, MOV, MKV) are allowed."
                if vid_file.size > 10 * 1024 * 1024:
                    return f"{file_label} size must be less than 10 MB."
            return None

        # Ensure at least 1 Gallery Photo & 1 Video exist
        if not service.gallery_image1 and not new_g1:
            messages.error(request, "At least 1 Gallery Photo is required!")
            return redirect('edit_service', service_id=service.id)

        if not service.service_video and not new_v1:
            messages.error(request, "At least 1 Promotional Video is required!")
            return redirect('edit_service', service_id=service.id)

        # Validate uploads
        for img, lbl in [(new_image, "Main Image"), (new_g1, "Gallery Image 1"), (new_g2, "Gallery Image 2"), (new_g3, "Gallery Image 3")]:
            err = validate_img(img, lbl)
            if err:
                messages.error(request, err)
                return redirect('edit_service', service_id=service.id)

        for vid, lbl in [(new_v1, "Video 1"), (new_v2, "Video 2")]:
            err = validate_vid(vid, lbl)
            if err:
                messages.error(request, err)
                return redirect('edit_service', service_id=service.id)

        if new_image: service.service_image = new_image
        if new_g1: service.gallery_image1 = new_g1
        if new_g2: service.gallery_image2 = new_g2
        if new_g3: service.gallery_image3 = new_g3
        if new_v1: service.service_video = new_v1
        if new_v2: service.service_video2 = new_v2

        # 💾 २. सेफ अपडेट (Safe Update without UUID crash)
        try:
            # Check valid UUID before querying DB
            def is_valid_uuid(val):
                if not val:
                    return False
                try:
                    uuid.UUID(str(val))
                    return True
                except ValueError:
                    return False

            category_obj = ad.Category.objects.filter(id=category_id).first() if is_valid_uuid(category_id) else service.category
            subcategory_obj = ad.SubCategory.objects.filter(id=subcategory_id).first() if is_valid_uuid(subcategory_id) else service.subcategory

            # सर्व्हिस डेटा अपडेट करणे
            service.service_name = service_name
            service.category = category_obj if category_obj else service.category
            service.subcategory = subcategory_obj
            
            if price:
                from decimal import Decimal
                try:
                    service.price = Decimal(str(price))
                except Exception:
                    pass

            # Available Days Extraction (Mon-Sun or All Days)
            selected_days = request.POST.getlist('available_days')
            if 'All Days' in selected_days or len(selected_days) == 7:
                available_days_str = "All Days (Mon - Sun)"
            elif selected_days:
                available_days_str = ", ".join(selected_days)
            else:
                available_days_str = request.POST.get('available_days_custom', '').strip() or "All Days (Mon - Sun)"

            service.service_area = service_area
            service.service_pincode = service_pincode
            service.experience = experience
            service.availability = availability
            service.available_days = available_days_str
            service.contact_number = contact_number
            service.skills_included = skills_included
            service.service_description = service_description
            
            service.save()  # सेव्ह करणे

            messages.success(request, "Service updated successfully! 🎉", extra_tags="service_updated")
            return redirect('my_services')

        except Exception as e:
            # 🔍 टर्मिनलवर नक्की काय चूक झाली ते प्रिंट करणे
            print("====================================")
            print("EXACT EDIT ERROR LOG:", str(e))
            print("====================================")
            messages.error(request, f"Failed to update service: {e}")

    # GET Request: डेटा टेम्पलेटला पाठवणे
    categories = ad.Category.objects.filter(is_active=True)
    subcategories = ad.SubCategory.objects.filter(category=service.category, is_active=True)

    context = {
        'provider': provider,
        'service': service,
        'categories': categories,
        'subcategories': subcategories
    }
    return render(request, 'service_provider/edit_service.html', context)


# toggle service active / inactive status
def toggle_service_status(request, service_id):
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    service = get_object_or_404(sr.AddService, id=service_id)
    service.is_active = not service.is_active
    service.save()

    status_str = "Active (Live on Website)" if service.is_active else "Inactive (Hidden from Website)"
    messages.success(request, f"Service '{service.service_name}' is now {status_str}! 🎉", extra_tags="service_updated")
    return redirect("my_services")


# delete service
def delete_service(request, service_id):
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    service = get_object_or_404(sr.AddService, id=service_id)
    service_name = service.service_name
    service.delete()

    messages.success(request, f"Service '{service_name}' deleted successfully! 🗑️", extra_tags="service_updated")
    return redirect("my_services")

# customer job leads for service provider
from customer.models import CustomServiceRequest, ServiceQuote


def provider_job_leads(request):
    """१. प्रोव्हायडरला त्याच्याच Pincode व Category च्या ग्राहकांच्या मागण्या दाखवणे"""
    provider_id = request.session.get("provider_id")
    if not provider_id:
        messages.error(request, "Please login as a Service Provider first.")
        return redirect('login')
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    if not provider:
        return redirect('login')
    # STRICT MATCHING: Pincode व Category जुळणाऱ्या प्रलंबित मागण्या
    job_leads = CustomServiceRequest.objects.filter(
        status='pending'
    )
    # १. Pincode Match (जर प्रोव्हायडर व ग्राहक दोघांचा Pincode उपलब्ध असेल)
    if provider.pincode:
        job_leads = job_leads.filter(customer__pincode=provider.pincode)
    # २. Category Match (उदा. Plumber -> Plumber)
    if provider.category and provider.category != 'other':
        job_leads = job_leads.filter(category__iexact=provider.category)
    job_leads = job_leads.order_by('-created_at')
    # प्रोव्हायडरने आधीच ज्या रिक्वेस्टवर कोटेशन पाठवले आहे ते तपासणे
    submitted_quote_request_ids = ServiceQuote.objects.filter(
        provider=provider
    ).values_list('request_id', flat=True)
    from .models import ProviderNotification
    notifications = ProviderNotification.objects.filter(provider=provider).order_by('-created_at')
    unread_notif_count = notifications.filter(is_read=False).count()

    context = {
        'provider': provider,
        'job_leads': job_leads,
        'submitted_quote_request_ids': submitted_quote_request_ids,
        'notifications': notifications,
        'unread_notif_count': unread_notif_count
    }
    return render(request, 'service_provider/job_leads.html', context)



def submit_service_quote(request):
    """२. प्रोव्हायडरने कोटेशन (रक्कम व मेसेज) सबमिट करणे (Standard POST Form)"""
    if request.method == 'POST':
        provider_id = request.session.get("provider_id")
        provider = us.ServiceProvider.objects.filter(id=provider_id).first()
        # १. लॉगिन चेक
        if not provider:
            messages.error(request, "Please log in as a Service Provider first.", extra_tags="provider_quote")
            return redirect('login')
        request_id = request.POST.get('request_id')
        quoted_price = request.POST.get('quoted_price', '').strip()
        message = request.POST.get('message', '').strip()
        estimated_time = request.POST.get('estimated_time', '').strip()
        # २. डेटा व्हॅलिडेशन
        if not request_id or not quoted_price:
            messages.error(request, "Quoted Price is required.", extra_tags="provider_quote")
            return redirect('provider_job_leads')
        custom_req = get_object_or_404(CustomServiceRequest, id=request_id)
        # -----------------------------------------------
        # ३. जर आधीच Quote पाठवले असेल तर ते Update करणे
        # -----------------------------------------------
        existing_quote = ServiceQuote.objects.filter(request=custom_req, provider=provider).first()
        if existing_quote:
            existing_quote.quoted_price = quoted_price
            existing_quote.message = message
            existing_quote.estimated_time = estimated_time
            existing_quote.save()
            messages.success(request, "Your quote price has been updated successfully!", extra_tags="provider_quote")
            return redirect('provider_job_leads')
        # -----------------------------------------------
        # ४. नवीन Quote डेटाबेसमध्ये सेव्ह करणे
        # -----------------------------------------------
        ServiceQuote.objects.create(
            request=custom_req,
            provider=provider,
            quoted_price=quoted_price,
            message=message,
            estimated_time=estimated_time,
            status='pending'
        )
        messages.success(request, "Quotation submitted successfully to the customer!", extra_tags="provider_quote")
        return redirect('provider_job_leads')
    return redirect('provider_job_leads')


def provider_accepted_jobs(request):
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    if not provider:
        return redirect("login")

    from customer.models import ServiceQuote, ProviderReview
    from .models import ProviderNotification

    # Show accepted, in_progress, work_completed, and completed jobs
    accepted_quotes_list = ServiceQuote.objects.filter(
        provider=provider,
        status__in=['accepted', 'in_progress', 'work_completed', 'completed']
    ).order_by('-created_at')
    
    reviews = ProviderReview.objects.filter(provider=provider, request__in=[q.request for q in accepted_quotes_list])
    review_map = {r.request_id: r for r in reviews}
    for q in accepted_quotes_list:
        q.customer_review = review_map.get(q.request_id)
    
    notifications = ProviderNotification.objects.filter(provider=provider).order_by('-created_at')

    # Mark unread notifications as read
    notifications.filter(is_read=False).update(is_read=True)

    # Pagination: 12 cards per page
    from django.core.paginator import Paginator
    paginator = Paginator(accepted_quotes_list, 12)
    page_number = request.GET.get('page')
    accepted_quotes = paginator.get_page(page_number)

    all_provider_reviews = ProviderReview.objects.filter(provider=provider).order_by('-created_at')
    provider_avg_rating = provider.get_avg_rating()
    provider_review_count = provider.get_review_count()

    context = {
        'provider': provider,
        'accepted_quotes': accepted_quotes,
        'notifications': notifications,
        'all_provider_reviews': all_provider_reviews,
        'provider_avg_rating': provider_avg_rating,
        'provider_review_count': provider_review_count
    }
    return render(request, 'service_provider/accepted_jobs.html', context)


def start_provider_job(request, quote_id):
    """१. प्रोव्हायडरने कामाला सुरुवात केल्यावर स्टेटस बदलणे व ग्राहकाला नोटिफिकेशन पाठवणे"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    if not provider:
        return redirect("login")

    from customer.models import ServiceQuote, CustomerNotification
    quote = get_object_or_404(ServiceQuote, id=quote_id, provider=provider)

    quote.status = 'in_progress'
    quote.save()

    custom_req = quote.request
    custom_req.status = 'in_progress'
    custom_req.save()

    # Create Customer Notification
    CustomerNotification.objects.create(
        customer=custom_req.customer,
        title="Work Started!",
        message=f"Service Provider {provider.full_name} has arrived at your location and started working on '{custom_req.title}'."
    )

    messages.success(request, f"Work marked as started for {custom_req.title}!", extra_tags="provider_quote")
    return redirect('provider_accepted_jobs')


def complete_provider_job(request, quote_id):
    """२. काम पूर्ण झाल्यावर मूळ रक्कम + अतिरिक्त खर्च (Extra Work) जोडणे"""
    if request.method == 'POST':
        provider_id = request.session.get("provider_id")
        provider = us.ServiceProvider.objects.filter(id=provider_id).first()
        if not provider:
            return redirect("login")

        from customer.models import ServiceQuote, CustomerNotification
        quote = get_object_or_404(ServiceQuote, id=quote_id, provider=provider)

        extra_charges_str = request.POST.get('extra_charges', '0').strip()
        extra_work_notes = request.POST.get('extra_work_notes', '').strip()

        try:
            extra_charges = float(extra_charges_str) if extra_charges_str else 0.0
        except ValueError:
            extra_charges = 0.0

        final_amount = float(quote.quoted_price) + extra_charges

        quote.extra_charges = extra_charges
        quote.final_amount = final_amount
        quote.extra_work_notes = extra_work_notes
        quote.status = 'work_completed'
        quote.save()

        custom_req = quote.request
        custom_req.status = 'work_completed'
        custom_req.save()

        # Create Customer Notification
        CustomerNotification.objects.create(
            customer=custom_req.customer,
            title="Work Completed - Bill Ready!",
            message=f"Service Provider {provider.full_name} finished '{custom_req.title}'. Total Final Bill: ₹{final_amount:.2f} (Base: ₹{quote.quoted_price} + Extra: ₹{extra_charges:.2f}). Please pay now."
        )

        messages.success(request, f"Work completed successfully! Total Final Bill generated: ₹{final_amount:.2f}", extra_tags="provider_quote")
        return redirect('provider_accepted_jobs')
    return redirect('provider_accepted_jobs')


def provider_earnings(request):
    """३. सर्व्हिस प्रोव्हायडरचे Earnings & Wallet आणि Payment History दाखवणे"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    if not provider:
        return redirect("login")

    from customer.models import ServiceQuote

    # Fetch all completed & paid quotes for this provider
    paid_quotes = ServiceQuote.objects.filter(
        provider=provider,
        payment_status='paid'
    ).order_by('-created_at')

    # Total Balance / Total Earnings Calculation
    total_earnings = 0.0
    online_earnings = 0.0
    cash_earnings = 0.0

    for q in paid_quotes:
        amt = float(q.final_amount) if q.final_amount else float(q.quoted_price)
        total_earnings += amt
        if q.payment_mode == 'online':
            online_earnings += amt
        else:
            cash_earnings += amt

    total_orders = paid_quotes.count()

    # Pagination: 20 transactions per page
    from django.core.paginator import Paginator
    paginator = Paginator(paid_quotes, 20)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    context = {
        'provider': provider,
        'total_earnings': total_earnings,
        'online_earnings': online_earnings,
        'cash_earnings': cash_earnings,
        'total_orders': total_orders,
        'transactions': transactions
    }
    return render(request, 'service_provider/earnings.html', context)


def download_receipt(request, quote_id):
    """पेमेंट पावती / Receipt Download for Provider"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")
    
    provider_id = request.session.get("provider_id")
    quote = get_object_or_404(ServiceQuote, id=quote_id, provider__id=provider_id, payment_status='paid')

    final_amt = quote.final_amount if quote.final_amount else quote.quoted_price

    context = {
        'quote': quote,
        'final_amount': final_amt,
    }
    return render(request, 'common/payment_receipt.html', context)


def provider_booking_requests(request):
    """सर्व्हिस प्रोव्हायडरला आलेल्या सर्व कस्टमर बुकिंग रिक्वेस्ट्स दाखवणे (Filter Buttons + Pagination सह)"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    if not provider:
        return redirect("login")

    status_filter = request.GET.get('status', 'all').strip().lower()

    all_bookings = us.DirectServiceBooking.objects.filter(
        provider_email=provider.email
    ).order_by('-created_at')

    # Counts for Filter Pills
    total_count = all_bookings.count()
    pending_count = all_bookings.filter(status='pending').count()
    accepted_count = all_bookings.filter(status='accepted').count()
    rejected_count = all_bookings.filter(status='cancelled').count()

    # Apply filter logic
    if status_filter == 'pending':
        booking_requests_list = all_bookings.filter(status='pending')
    elif status_filter == 'accepted':
        booking_requests_list = all_bookings.filter(status='accepted')
    elif status_filter in ['rejected', 'cancelled']:
        booking_requests_list = all_bookings.filter(status='cancelled')
        status_filter = 'rejected'
    else:
        status_filter = 'all'
        booking_requests_list = all_bookings

    # Pagination: 6 items per page
    from django.core.paginator import Paginator
    paginator = Paginator(booking_requests_list, 6)
    page_number = request.GET.get('page')
    booking_requests = paginator.get_page(page_number)

    context = {
        'provider': provider,
        'booking_requests': booking_requests,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count
    }
    return render(request, 'service_provider/booking_requests.html', context)



def accept_booking_request(request, booking_id):
    """प्रोव्हायडरने बुकिंग रिक्वेस्ट Accept करणे (मोजून स्टेटस 'accepted' करणे)"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    
    booking = get_object_or_404(us.DirectServiceBooking, id=booking_id, provider_email=provider.email)
    booking.status = 'accepted'
    booking.save()

    # 🔔 १. Customer ला Notification पाठवणे
    try:
        from customer.models import CustomerNotification
        CustomerNotification.objects.create(
            customer=booking.customer,
            title="Booking Request Accepted! 🎉",
            message=f"Service Provider {provider.full_name} ({provider.mobile}) has ACCEPTED your booking #{booking.id} for '{booking.service.service_name}'. Scheduled: {booking.booking_date} ({booking.time_slot})."
        )
    except Exception as e:
        print("Customer Notification Error:", e)

    # 🔔 २. Provider ला Confirmation Notification पाठवणे
    try:
        from .models import ProviderNotification
        ProviderNotification.objects.create(
            provider=provider,
            title=f"Booking Accepted! ✅ (#{booking.id})",
            message=f"You accepted Booking #{booking.id} for customer {booking.customer.full_name} ({booking.customer.mobile}). Scheduled for {booking.booking_date} ({booking.time_slot})."
        )
    except Exception as e:
        print("Provider Notification Error:", e)

    messages.success(request, f"🎉 Booking #{booking.id} has been accepted successfully!", extra_tags="booking_accept")
    return redirect('provider_my_bookings')


def reject_booking_request(request, booking_id):
    """प्रोव्हायडरने बुकिंग रिक्वेस्ट Reject करणे (स्टेटस 'cancelled' करून रिजेक्टेड दाखवणे)"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    
    booking = get_object_or_404(us.DirectServiceBooking, id=booking_id, provider_email=provider.email)
    booking.status = 'cancelled'
    booking.save()

    # 🔔 Customer ला Rejection Notification पाठवणे
    try:
        from customer.models import CustomerNotification
        CustomerNotification.objects.create(
            customer=booking.customer,
            title="Booking Request Rejected ❌",
            message=f"Your booking request #{booking.id} for '{booking.service.service_name}' was rejected by service provider {provider.full_name}. You can browse and book other service providers."
        )
    except Exception as e:
        print("Customer Notification Error:", e)

    messages.info(request, f"Booking #{booking.id} was rejected.", extra_tags="booking_reject")
    return redirect('provider_booking_requests')


def provider_my_bookings(request):
    """प्रोव्हायडरने Accept केलेल्या सर्व बुकिंग्ज (My Bookings)"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    if not provider:
        return redirect("login")

    my_bookings = us.DirectServiceBooking.objects.filter(
        provider_email=provider.email,
        status__in=['accepted', 'in_progress', 'completed']
    ).order_by('-created_at')

    context = {
        'provider': provider,
        'my_bookings': my_bookings
    }
    return render(request, 'service_provider/my_bookings.html', context)


def complete_direct_booking(request, booking_id):
    """काम पूर्ण झाल्यावर प्रोव्हायडरने अंतिम रक्कम (Final Amount) टाकून 'Complete Service' करणे"""
    if not request.session.get("provider_logged_in"):
        return redirect("login")

    provider_id = request.session.get("provider_id")
    provider = us.ServiceProvider.objects.filter(id=provider_id).first()
    
    booking = get_object_or_404(us.DirectServiceBooking, id=booking_id, provider_email=provider.email)
    
    if request.method == "POST":
        final_amount = request.POST.get('final_amount', '0').strip()
        if final_amount:
            try:
                booking.total_amount = float(final_amount)
            except ValueError:
                pass

        booking.status = 'completed'
        booking.payment_status = 'paid'
        booking.save()

        # 🔔 Customer ला Payment Completed Notification पाठवणे
        try:
            from customer.models import CustomerNotification
            CustomerNotification.objects.create(
                customer=booking.customer,
                title="Service Completed & Payment Recorded! 💵",
                message=f"Service Provider {provider.full_name} completed your service '{booking.service.service_name}' (Booking #{booking.id}). Total Payment: ₹{booking.total_amount} recorded via {booking.payment_mode.upper()}. Thank you!"
            )
        except Exception as e:
            print("Customer Notification Error:", e)

        # 🔔 Provider ला Payment Received Notification पाठवणे
        try:
            from .models import ProviderNotification
            ProviderNotification.objects.create(
                provider=provider,
                title=f"Payment Received: ₹{booking.total_amount}! 💰",
                message=f"Booking #{booking.id} completed! Payment of ₹{booking.total_amount} received from customer {booking.customer.full_name} via {booking.payment_mode.upper()}."
            )
        except Exception as e:
            print("Provider Notification Error:", e)

        messages.success(request, f"🎉 Booking #{booking.id} marked completed with Final Amount ₹{booking.total_amount}!", extra_tags="booking_complete")
        return redirect('provider_my_bookings')

    booking.status = 'completed'
    booking.payment_status = 'paid'
    booking.save()

    # 🔔 Customer ला Notification
    try:
        from customer.models import CustomerNotification
        CustomerNotification.objects.create(
            customer=booking.customer,
            title="Service Completed & Payment Recorded! 💵",
            message=f"Service Provider {provider.full_name} completed your service '{booking.service.service_name}' (Booking #{booking.id}). Total Payment: ₹{booking.total_amount} recorded via {booking.payment_mode.upper()}."
        )
    except Exception as e:
        print("Customer Notification Error:", e)

    # 🔔 Provider ला Notification
    try:
        from .models import ProviderNotification
        ProviderNotification.objects.create(
            provider=provider,
            title=f"Payment Received: ₹{booking.total_amount}! 💰",
            message=f"Booking #{booking.id} completed! Payment of ₹{booking.total_amount} received from customer {booking.customer.full_name} via {booking.payment_mode.upper()}."
        )
    except Exception as e:
        print("Provider Notification Error:", e)

    messages.success(request, f"🎉 Booking #{booking.id} marked as completed!", extra_tags="booking_complete")
    return redirect('provider_my_bookings')


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def mark_provider_notifications_read(request):
    """Notification bell click केल्यावर सर्व Unread Provider Notifications Read करणे"""
    provider_id = request.session.get("provider_id")
    if provider_id:
        from .models import ProviderNotification
        ProviderNotification.objects.filter(provider_id=provider_id, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)