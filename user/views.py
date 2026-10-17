from django.shortcuts import render,redirect
from . import models as us

import random
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from datetime import timedelta

from django.http import JsonResponse

from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail

from django.utils import timezone
from adminpanel import models as ad



import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404
 
from service_provider.models import AddService


# Create your views here.

def index(req):
    categories = ad.Category.objects.filter(is_active=True)
    return render(req, 'user/index.html', {'categories': categories})

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from service_provider import models as sr

def service(request):
    cat_id = request.GET.get('cat_id')
    search_query = request.GET.get('search', '').strip()
    
    services_list = sr.AddService.objects.filter(is_active=True)
    categories = ad.Category.objects.filter(is_active=True)
    
    if cat_id:
        services_list = services_list.filter(category_id=cat_id)
        
    if search_query:
        from django.db.models import Q
        services_list = services_list.filter(
            Q(service_name__icontains=search_query) |
            Q(service_description__icontains=search_query) |
            Q(skills_included__icontains=search_query)
        )
        
    services_list = list(services_list.order_by('-created_at'))
    
    # 📍 Get Logged-in Customer Pincode for Smart Priority Matching
    customer_pincode = None
    customer_id = request.session.get("customer_id")
    if customer_id:
        cust_obj = us.CustomerRegistration.objects.filter(id=customer_id).first()
        if cust_obj and cust_obj.pincode:
            customer_pincode = str(cust_obj.pincode).strip()
    elif request.user.is_authenticated:
        cust_obj = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()
        if cust_obj and cust_obj.pincode:
            customer_pincode = str(cust_obj.pincode).strip()

    # Map Provider Details & Separate by Customer Pincode Match
    providers = us.ServiceProvider.objects.all()
    provider_map = {p.email.lower(): p for p in providers}

    pincode_matched_services = []
    other_services = []

    for srv in services_list:
        p_obj = provider_map.get(str(srv.provider_email).lower())
        if p_obj:
            srv.provider_full_name = p_obj.full_name
            srv.provider_avatar = p_obj.profile_image.url if p_obj.profile_image else None
            srv.provider_avg_rating = p_obj.get_avg_rating()
            srv.provider_review_count = p_obj.get_review_count()
            srv.provider_pincode = str(p_obj.pincode).strip() if p_obj.pincode else None
        else:
            srv.provider_full_name = "Verified Provider"
            srv.provider_avatar = None
            srv.provider_avg_rating = 0.0
            srv.provider_review_count = 0
            srv.provider_pincode = None

        # Check Service Pincodes (multi-pincode support) or Provider Profile Pincode
        srv_pincodes = [pin.strip() for pin in str(srv.service_pincode).split(',') if pin.strip()] if srv.service_pincode else []
        is_match = False
        if customer_pincode:
            if customer_pincode in srv_pincodes:
                is_match = True
            elif srv.provider_pincode and srv.provider_pincode == customer_pincode:
                is_match = True
        srv.is_pincode_match = is_match

        if srv.is_pincode_match:
            pincode_matched_services.append(srv)
        else:
            other_services.append(srv)

    # Priority 1: Customer Pincode Matched Services first! Priority 2: Other Services
    if customer_pincode:
        final_services_list = pincode_matched_services + other_services
    else:
        final_services_list = services_list

    # Pagination: 12 cards per page
    paginator = Paginator(final_services_list, 12)
    page_number = request.GET.get('page')
    try:
        services = paginator.page(page_number)
    except PageNotAnInteger:
        services = paginator.page(1)
    except EmptyPage:
        services = paginator.page(paginator.num_pages)

    categories = ad.Category.objects.filter(is_active=True)
    
    context = {
        'services': services,
        'categories': categories,
        'selected_cat_id': cat_id,
        'search_query': search_query,
        'customer_pincode': customer_pincode
    }
    return render(request, "user/service.html", context)

def view_service(request):
    service_id = request.GET.get('service_id')
    
    service_obj = None
    if service_id:
        try:
            service_obj = sr.AddService.objects.get(id=service_id, is_active=True)
        except (sr.AddService.DoesNotExist, ValueError):
            service_obj = sr.AddService.objects.filter(is_active=True).first()
    else:
        service_obj = sr.AddService.objects.filter(is_active=True).first()
        
    provider_info = None
    related_services = []
    reviews_list = []
    provider_avg_rating = 0.0
    provider_review_count = 0

    if service_obj:
        provider_info = us.ServiceProvider.objects.filter(email__iexact=service_obj.provider_email).first()
        if provider_info:
            from customer import models as cs_mod
            reviews_list = cs_mod.ProviderReview.objects.filter(provider=provider_info).select_related('customer').order_by('-created_at')
            provider_avg_rating = provider_info.get_avg_rating()
            provider_review_count = provider_info.get_review_count()

        related_services = sr.AddService.objects.filter(category=service_obj.category, is_active=True).exclude(id=service_obj.id)[:10]
        if not related_services.exists():
            related_services = sr.AddService.objects.filter(is_active=True).exclude(id=service_obj.id)[:10]

        providers = us.ServiceProvider.objects.all()
        provider_map = {p.email.lower(): p.full_name for p in providers}
        for rel in related_services:
            rel.provider_full_name = provider_map.get(str(rel.provider_email).lower(), "Verified Provider")

    skills_list = []
    if service_obj and service_obj.skills_included:
        if ',' in service_obj.skills_included:
            skills_list = [s.strip() for s in service_obj.skills_included.split(',') if s.strip()]
        elif '\n' in service_obj.skills_included:
            skills_list = [s.strip() for s in service_obj.skills_included.split('\n') if s.strip()]
        else:
            skills_list = [service_obj.skills_included.strip()]

    context = {
        'service': service_obj,
        'provider_info': provider_info,
        'related_services': related_services,
        'reviews_list': reviews_list,
        'provider_avg_rating': provider_avg_rating,
        'provider_review_count': provider_review_count,
        'skills_list': skills_list
    }
    return render(request, "user/service_detail.html", context)

# category start here 


def category(req):
    categories = ad.Category.objects.filter(is_active=True)
    return render(req,"user/category.html", {'categories': categories})


def subcategory(request):
    cat_id = request.GET.get('cat_id')
    subcat_id = request.GET.get('subcat_id')
    
    category_obj = None
    if cat_id:
        try:
            category_obj = ad.Category.objects.get(id=cat_id)
        except (ad.Category.DoesNotExist, ValueError):
            category_obj = ad.Category.objects.filter(is_active=True).first()
    else:
        category_obj = ad.Category.objects.filter(is_active=True).first()
        
    subcategories_list = ad.SubCategory.objects.filter(category=category_obj, is_active=True) if category_obj else []
    
    selected_subcat = None
    if subcat_id:
        selected_subcat = ad.SubCategory.objects.filter(id=subcat_id, is_active=True).first()

    # Dynamic real services query for this category and subcategory
    services_list = []
    if category_obj:
        if selected_subcat:
            services_list = list(sr.AddService.objects.filter(category=category_obj, subcategory=selected_subcat, is_active=True).order_by('-created_at'))
        else:
            services_list = list(sr.AddService.objects.filter(category=category_obj, is_active=True).order_by('-created_at'))

    # 📍 Get Logged-in Customer Pincode for Smart Priority Matching
    customer_pincode = None
    customer_id = request.session.get("customer_id")
    if customer_id:
        cust_obj = us.CustomerRegistration.objects.filter(id=customer_id).first()
        if cust_obj and cust_obj.pincode:
            customer_pincode = str(cust_obj.pincode).strip()
    elif request.user.is_authenticated:
        cust_obj = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                   us.CustomerRegistration.objects.filter(email=request.user.email).first()
        if cust_obj and cust_obj.pincode:
            customer_pincode = str(cust_obj.pincode).strip()

    # Attach provider rating, review count & Pincode Priority
    providers = us.ServiceProvider.objects.all()
    provider_map = {p.email.lower(): p for p in providers}

    pincode_matched_services = []
    other_services = []

    for srv in services_list:
        p_obj = provider_map.get(str(srv.provider_email).lower())
        if p_obj:
            srv.provider_name = p_obj.full_name
            srv.provider_avatar = p_obj.profile_image.url if p_obj.profile_image else None
            srv.provider_avg_rating = p_obj.get_avg_rating()
            srv.provider_review_count = p_obj.get_review_count()
            srv.provider_pincode = str(p_obj.pincode).strip() if p_obj.pincode else None
        else:
            srv.provider_name = srv.provider_email
            srv.provider_avatar = None
            srv.provider_avg_rating = 0.0
            srv.provider_review_count = 0
            srv.provider_pincode = None

        # Check Service Pincodes (multi-pincode support) or Provider Profile Pincode
        srv_pincodes = [pin.strip() for pin in str(srv.service_pincode).split(',') if pin.strip()] if srv.service_pincode else []
        is_match = False
        if customer_pincode:
            if customer_pincode in srv_pincodes:
                is_match = True
            elif srv.provider_pincode and srv.provider_pincode == customer_pincode:
                is_match = True
        srv.is_pincode_match = is_match

        if srv.is_pincode_match:
            pincode_matched_services.append(srv)
        else:
            other_services.append(srv)

    # Priority 1: Customer Pincode Matched Services first! Priority 2: Other Services
    if customer_pincode:
        final_services_list = pincode_matched_services + other_services
    else:
        final_services_list = services_list

    context = {
        'category': category_obj,
        'subcategories': subcategories_list,
        'services': final_services_list,
        'selected_subcat': selected_subcat,
        'customer_pincode': customer_pincode
    }
    return render(request, 'user/subcategory.html', context)


def become_provider(req):
    categories = ad.Category.objects.filter(is_active=True)
    return render(req, "user/service_provider_registration.html", {'categories': categories})


def provider_register(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        })

    # -----------------------------
    # CHECK OTP VERIFICATION
    # -----------------------------

    if not request.session.get(
        "provider_email_verified"
    ):

        return JsonResponse({
            "success": False,
            "message": "Please verify your email with OTP first."
        })

    verified_email = request.session.get(
        "provider_verified_email"
    )

    # -----------------------------
    # FORM DATA
    # -----------------------------

    email = request.POST.get(
        "email",
        ""
    ).strip().lower()

    full_name = request.POST.get(
        "full_name",
        ""
    ).strip()

    business_name = request.POST.get(
        "business_name",
        ""
    ).strip()

    category = request.POST.get(
        "category",
        ""
    ).strip()
    # subcategory = request.POST.get("subcategory", "").strip()
    password = request.POST.get(
            "password",
            ""
        ).strip()

    other_category = request.POST.get(
        "other_category",
        ""
    ).strip()

    mobile = request.POST.get(
        "mobile",
        ""
    ).strip()

    city_area = request.POST.get(
        "city_area",
        ""
    ).strip()

    pincode = request.POST.get(
        "pincode",
        ""
    ).strip()

    profile_image = request.FILES.get(
    "profile_image"
    )

    experience = request.POST.get(
        "experience",
        ""
    ).strip()

    # -----------------------------
    # EMAIL VERIFICATION CHECK
    # -----------------------------

    if email != verified_email:

        return JsonResponse({
            "success": False,
            "message": "Email verification mismatch."
        })

    # -----------------------------
    # VALIDATION
    # -----------------------------

    if len(full_name) < 3:

        return JsonResponse({
            "success": False,
            "message": "Please enter a valid full name."
        })

    if not business_name:

        return JsonResponse({
            "success": False,
            "message": "Business name is required."
        })

    if not category:

        return JsonResponse({
            "success": False,
            "message": "Please select a service category."
        })

    # Other category validation
    if category == "other" and not other_category:

        return JsonResponse({
            "success": False,
            "message": "Please specify your other category."
        })

    # Mobile validation
    if not mobile.isdigit() or len(mobile) != 10:

        return JsonResponse({
            "success": False,
            "message": "Mobile number must contain exactly 10 digits."
        })

    # -----------------------------
    # CHECK DUPLICATE EMAIL AGAIN
    # -----------------------------

    if us.ServiceProvider.objects.filter(
        email=email
    ).exists():

        return JsonResponse({
            "success": False,
            "already_registered": True,
            "message": "This email is already registered."
        })

    # -----------------------------
    # CHECK DUPLICATE MOBILE
    # -----------------------------

    if us.ServiceProvider.objects.filter(
        mobile=mobile
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "This mobile number is already registered."
        })

    # -----------------------------
    # CREATE SERVICE PROVIDER
    # -----------------------------

    try:

        provider = us.ServiceProvider.objects.create(

            email=email,

            full_name=full_name,

            business_name=business_name,
            profile_image=profile_image,
            category=category,
            # subcategory=subcategory,
            other_category=(
                other_category
                if category == "other"
                else None
            ),

            mobile=mobile,
            password=make_password(password),

            city_area=city_area,

            pincode=pincode,

            experience=experience,

            # subcategory=(
            #     subcategory
            #     if category != "other"
            #     else None
            # ),

            is_approved=False,
            approval_status="pending"
        )

        # -----------------------------
        # DELETE OTP
        # -----------------------------

        us.ProviderRegistrationOTP.objects.filter(
            email=email
        ).delete()

        # -----------------------------
        # CLEAR SESSION
        # -----------------------------

        request.session.pop(
            "provider_email_verified",
            None
        )

        request.session.pop(
            "provider_verified_email",
            None
        )

        return JsonResponse({
            "success": True,
            "message": "Service Provider registration successful.",
            "redirect_url": "/login/"
        })

    except Exception as e:

        print("REGISTRATION ERROR:", e)

        return JsonResponse({
            "success": False,
            "message": "Registration failed. Please try again."
        })


def send_provider_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        })

    email = request.POST.get("email", "").strip().lower()

    # -----------------------------
    # EMAIL REQUIRED
    # -----------------------------

    if not email:
        return JsonResponse({
            "success": False,
            "message": "Please enter your email address."
        })

    # -----------------------------
    # CHECK EMAIL ALREADY REGISTERED
    # -----------------------------

    if us.ServiceProvider.objects.filter(email=email).exists():

        return JsonResponse({
            "success": False,
            "already_registered": True,
            "message": "This email is already registered."
        })

    # -----------------------------
    # GENERATE 6 DIGIT OTP
    # -----------------------------

    otp = str(random.randint(100000, 999999))

    # -----------------------------
    # SAVE / UPDATE OTP
    # -----------------------------

    us.ProviderRegistrationOTP.objects.update_or_create(
        email=email,
        defaults={
            "otp": otp,
            "created_at": timezone.now()
        }
    )

    # -----------------------------
    # EMAIL MESSAGE
    # -----------------------------

    subject = "Service Provider Registration OTP"

    message = f"""
Hello,

Thank you for registering as a Service Provider.

Your verification OTP is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this OTP with anyone.

Regards,
Local Service Marketplace
"""

    # -----------------------------
    # SEND EMAIL
    # -----------------------------

    try:

        send_mail(
            subject,
            message,
            None,
            [email],
            fail_silently=False
        )

        return JsonResponse({
            "success": True,
            "message": "OTP sent successfully to your email."
        })

    except Exception as e:

        print("EMAIL ERROR:", e)

        return JsonResponse({
            "success": False,
            "message": "Unable to send OTP. Please try again."
        })


def verify_provider_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        })

    email = request.POST.get(
        "email",
        ""
    ).strip().lower()

    entered_otp = request.POST.get(
        "otp",
        ""
    ).strip()

    # -----------------------------
    # REQUIRED CHECK
    # -----------------------------

    if not email or not entered_otp:

        return JsonResponse({
            "success": False,
            "message": "Email and OTP are required."
        })

    # -----------------------------
    # CHECK EMAIL ALREADY REGISTERED
    # -----------------------------

    if us.ServiceProvider.objects.filter(
        email=email
    ).exists():

        return JsonResponse({
            "success": False,
            "already_registered": True,
            "message": "This email is already registered."
        })

    # -----------------------------
    # GET OTP
    # -----------------------------

    try:

        otp_obj = us.ProviderRegistrationOTP.objects.get(
            email=email
        )

    except us.ProviderRegistrationOTP.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "OTP not found. Please request a new OTP."
        })

    # -----------------------------
    # OTP EXPIRY - 5 MINUTES
    # -----------------------------

    expiry_time = (
        otp_obj.created_at +
        timedelta(minutes=5)
    )

    if timezone.now() > expiry_time:

        otp_obj.delete()

        return JsonResponse({
            "success": False,
            "message": "OTP has expired. Please request a new OTP."
        })

    # -----------------------------
    # CHECK OTP
    # -----------------------------

    if entered_otp != otp_obj.otp:

        return JsonResponse({
            "success": False,
            "message": "Invalid OTP. Please enter the correct OTP."
        })

    # -----------------------------
    # OTP VERIFIED
    # -----------------------------

    request.session[
        "provider_email_verified"
    ] = True

    request.session[
        "provider_verified_email"
    ] = email

    return JsonResponse({
        "success": True,
        "message": "Email verified successfully."
    })



# provider login start

def provider_login(request):

    if request.method == "POST":

        email = request.POST.get(
            "provider-email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "provider-password",
            ""
        )

        try:

            provider = us.ServiceProvider.objects.get(
                email=email
            )

        except us.ServiceProvider.DoesNotExist:

            messages.error(
                request,
                "Invalid email or password.",
                extra_tags="provider_login"
            )

            return redirect("login")

        # Password check
        if not check_password(
            password,
            provider.password
        ):

            messages.error(
                request,
                "Invalid email or password.",
                extra_tags="provider_login"
            )

            return redirect("login")

        # --------------------------------
        # ALL CATEGORIES REQUIRE ADMIN APPROVAL
        # --------------------------------

        if not provider.is_approved or provider.approval_status != "approved":

            if provider.approval_status == "rejected":
                messages.error(
                    request,
                    "Your registration request has been rejected by admin. Please contact support.",
                    extra_tags="provider_login"
                )
            else:
                messages.warning(
                    request,
                    "Your registration is waiting for admin approval. Please try logging in after approval.",
                    extra_tags="provider_login"
                )

            return redirect("login")

        # --------------------------------
        # LOGIN SUCCESS
        # --------------------------------

        request.session["provider_id"] = provider.id

        request.session["provider_email"] = provider.email

        request.session["provider_logged_in"] = True

        return redirect("provider_dashboard")

    return redirect("login")

import random
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth.models import User

# टीप: तुमच्या ॲपचे मॉडेल्स इथे इम्पोर्ट करा (उदा. import .models as us)


def customer_register(request):

    if request.method == "GET":
        return render(request, 'user/customer_register.html')

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        })

    # -----------------------------
    # CHECK OTP VERIFICATION
    # -----------------------------

    if not request.session.get("customer_email_verified"):

        return JsonResponse({
            "success": False,
            "message": "Please verify your email with OTP first."
        })

    verified_email = request.session.get("customer_verified_email")

    # -----------------------------
    # FORM DATA
    # -----------------------------

    email = request.POST.get("email", "").strip().lower()
    full_name = request.POST.get("full_name", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    password = request.POST.get("password", "").strip()
    
    profile_photo = request.FILES.get("profile_photo")
    gender = request.POST.get("gender", "").strip()
    dob = request.POST.get("dob", "").strip()

    address = request.POST.get("address", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()
    pincode = request.POST.get("pincode", "").strip()

    # -----------------------------
    # EMAIL VERIFICATION CHECK
    # -----------------------------

    if email != verified_email:

        return JsonResponse({
            "success": False,
            "message": "Email verification mismatch."
        })

    # -----------------------------
    # VALIDATION
    # -----------------------------

    if len(full_name) < 3:

        return JsonResponse({
            "success": False,
            "message": "Please enter a valid full name."
        })

    if not password or len(password) < 6:

        return JsonResponse({
            "success": False,
            "message": "Password must be at least 6 characters long."
        })

    # Mobile validation
    if not mobile.isdigit() or len(mobile) != 10:

        return JsonResponse({
            "success": False,
            "message": "Mobile number must contain exactly 10 digits."
        })

    # Address validation
    if not address or not city or not state or not pincode:

        return JsonResponse({
            "success": False,
            "message": "Please provide complete address details (Address, City, State, Pincode)."
        })

    # -----------------------------
    # CHECK DUPLICATE EMAIL
    # -----------------------------

    if us.CustomerRegistration.objects.filter(email=email).exists() or us.CustomerRegistration.objects.filter(user__email=email).exists():

        return JsonResponse({
            "success": False,
            "already_registered": True,
            "message": "This email is already registered."
        })

    # Clean up orphan User object if profile was deleted
    User.objects.filter(email=email).delete()

    # -----------------------------
    # CHECK DUPLICATE MOBILE
    # -----------------------------

    if us.CustomerRegistration.objects.filter(mobile=mobile).exists():

        return JsonResponse({
            "success": False,
            "message": "This mobile number is already registered."
        })

    # -----------------------------
    # CREATE USER & CUSTOMER PROFILE
    # -----------------------------

    try:
        # 1. Create Django Auth User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        # 2. Create Customer Profile linked to User
        customer = us.CustomerRegistration.objects.create(
            user=user,
            email=email,
            password=make_password(password),
            full_name=full_name,
            mobile=mobile,
            profile_photo=profile_photo,
            gender=gender if gender else None,
            dob=dob if dob else None,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            is_email_verified=True
        )

        # -----------------------------
        # DELETE OTP
        # -----------------------------

        us.EmailOTP.objects.filter(email=email).delete()

        # -----------------------------
        # AUTO LOGIN & CLEAR SESSION
        # -----------------------------

        request.session["customer_id"] = customer.id
        request.session["customer_email"] = customer.email
        request.session["customer_name"] = customer.full_name
        request.session["customer_photo"] = customer.profile_photo.url if customer.profile_photo else None
        request.session["customer_logged_in"] = True
        if user:
            from django.contrib.auth import login as django_login
            django_login(request, user)

        request.session.pop("customer_email_verified", None)
        request.session.pop("customer_verified_email", None)

        messages.success(request, f"Welcome {customer.full_name}! Account created successfully.", extra_tags="customer_login")

        return JsonResponse({
            "success": True,
            "message": "Customer registration successful! Welcome to Marketplace.",
            "redirect_url": "/"
        })

    except Exception as e:

        print("REGISTRATION ERROR:", e)

        return JsonResponse({
            "success": False,
            "message": "Registration failed. Please try again."
        })


def send_customer_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        })

    email = request.POST.get("email", "").strip().lower()

    # -----------------------------
    # EMAIL REQUIRED
    # -----------------------------

    if not email:
        return JsonResponse({
            "success": False,
            "message": "Please enter your email address."
        })

    # -----------------------------
    # CHECK EMAIL ALREADY REGISTERED
    # -----------------------------

    if us.CustomerRegistration.objects.filter(email=email).exists() or us.CustomerRegistration.objects.filter(user__email=email).exists():

        return JsonResponse({
            "success": False,
            "already_registered": True,
            "message": "This email is already registered."
        })

    # -----------------------------
    # GENERATE 6 DIGIT OTP
    # -----------------------------

    otp = str(random.randint(100000, 999999))

    # -----------------------------
    # SAVE / UPDATE OTP IN EmailOTP
    # -----------------------------

    us.EmailOTP.objects.update_or_create(
        email=email,
        defaults={
            "otp": otp,
            "created_at": timezone.now(),
            "is_verified": False
        }
    )

    # -----------------------------
    # EMAIL MESSAGE
    # -----------------------------

    subject = "Customer Registration OTP"

    message = f"""
Hello,

Thank you for registering as a Customer.

Your verification OTP is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this OTP with anyone.

Regards,
Local Service Marketplace
"""

    # -----------------------------
    # SEND EMAIL
    # -----------------------------

    try:

        send_mail(
            subject,
            message,
            None,
            [email],
            fail_silently=False
        )

        return JsonResponse({
            "success": True,
            "message": "OTP sent successfully to your email."
        })

    except Exception as e:

        print("EMAIL ERROR:", e)

        return JsonResponse({
            "success": False,
            "message": "Unable to send OTP. Please try again."
        })


def verify_customer_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        })

    email = request.POST.get("email", "").strip().lower()
    entered_otp = request.POST.get("otp", "").strip()

    # -----------------------------
    # REQUIRED CHECK
    # -----------------------------

    if not email or not entered_otp:

        return JsonResponse({
            "success": False,
            "message": "Email and OTP are required."
        })

    # -----------------------------
    # CHECK EMAIL ALREADY REGISTERED
    # -----------------------------

    if us.CustomerRegistration.objects.filter(email=email).exists() or us.CustomerRegistration.objects.filter(user__email=email).exists():

        return JsonResponse({
            "success": False,
            "already_registered": True,
            "message": "This email is already registered."
        })

    # -----------------------------
    # GET OTP FROM EmailOTP
    # -----------------------------

    try:

        otp_obj = us.EmailOTP.objects.get(email=email)

    except us.EmailOTP.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "OTP not found. Please request a new OTP."
        })

    # -----------------------------
    # OTP EXPIRY CHECK
    # -----------------------------

    if not otp_obj.is_valid():

        otp_obj.delete()

        return JsonResponse({
            "success": False,
            "message": "OTP has expired. Please request a new OTP."
        })

    # -----------------------------
    # CHECK OTP MATCH
    # -----------------------------

    if entered_otp != otp_obj.otp:

        return JsonResponse({
            "success": False,
            "message": "Invalid OTP. Please enter the correct OTP."
        })

    # -----------------------------
    # OTP VERIFIED
    # -----------------------------

    otp_obj.is_verified = True
    otp_obj.save()

    request.session["customer_email_verified"] = True
    request.session["customer_verified_email"] = email

    return JsonResponse({
        "success": True,
        "message": "Email verified successfully."
    })

def customer_login(request):
    if request.method == "GET":
        return render(request, 'user/login.html')

    if request.method == "POST":
        email = request.POST.get("customer-email", "").strip().lower()
        password = request.POST.get("customer-password", "")

        # 1. Validation Check
        if not email or not password:
            messages.error(
                request, 
                "Please enter both email and password.", 
                extra_tags="customer_login"
            )
            return render(request, 'user/login.html')

        # 2. Find Customer in Database (CustomerRegistration or User)
        customer = us.CustomerRegistration.objects.filter(email=email).first()
        if not customer:
            customer = us.CustomerRegistration.objects.filter(user__email=email).first()

        user_obj = None
        if not customer:
            user_obj = User.objects.filter(email=email).first()
            if not user_obj:
                messages.error(
                    request, 
                    "Invalid email or password.", 
                    extra_tags="customer_login"
                )
                return render(request, 'user/login.html')

        # 3. Password Verification (check both CustomerRegistration password & User password)
        password_valid = False
        if customer and customer.password:
            password_valid = check_password(password, customer.password)

        if not password_valid and customer and customer.user and customer.user.password:
            password_valid = check_password(password, customer.user.password)

        if not password_valid and user_obj and user_obj.password:
            password_valid = check_password(password, user_obj.password)

        if not password_valid:
            messages.error(
                request, 
                "Invalid email or password.", 
                extra_tags="customer_login"
            )
            return render(request, 'user/login.html')

        # 4. Login Success -> Set Session Data
        if customer:
            request.session["customer_id"] = customer.id
            request.session["customer_email"] = customer.email
            request.session["customer_name"] = customer.full_name
            request.session["customer_photo"] = customer.profile_photo.url if customer.profile_photo else None
            request.session["customer_logged_in"] = True
            if customer.user:
                from django.contrib.auth import login as django_login
                django_login(request, customer.user)
        elif user_obj:
            request.session["customer_id"] = user_obj.id
            request.session["customer_email"] = user_obj.email
            request.session["customer_name"] = user_obj.first_name or user_obj.username
            request.session["customer_logged_in"] = True
            from django.contrib.auth import login as django_login
            django_login(request, user_obj)

        messages.success(
            request, 
            "Customer login successful! Welcome back.", 
            extra_tags="customer_login"
        )
        
        # Redirect directly to Landing Page (Home Page)
        return redirect("user_index")

    return render(request, 'user/login.html')


# cusotmer form fill service provider posted



razorpay_client = razorpay.Client(
    auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', ''))
)

def book_service_api(request, service_id):
    """१. कस्टमरकडून सर्व्हिस बुकिंग रिक्वेस्ट सेव्ह करणे व प्रोव्हायडरकडे पाठवणे"""
    if request.method == 'POST':
        customer_id = request.session.get("customer_id")
        customer = None
        if customer_id:
            customer = us.CustomerRegistration.objects.filter(id=customer_id).first()
        elif request.user.is_authenticated:
            customer = us.CustomerRegistration.objects.filter(user=request.user).first() or \
                       us.CustomerRegistration.objects.filter(email=request.user.email).first()

        if not customer:
            return JsonResponse({'success': False, 'message': 'Please log in as a customer before booking this service.'})

        service_obj = AddService.objects.filter(id=service_id).first()
        if not service_obj:
            return JsonResponse({'success': False, 'message': 'Selected service could not be found.'})

        booking_date = request.POST.get('booking_date', '').strip()
        time_slot = request.POST.get('time_slot', '').strip()
        customer_address = request.POST.get('customer_address', '').strip()
        notes = request.POST.get('notes', '').strip()
        problem_photo = request.FILES.get('problem_photo')
        payment_mode = request.POST.get('payment_mode', 'cash')

        if not booking_date or not time_slot or not customer_address:
            return JsonResponse({'success': False, 'message': 'Please select a date, time slot, and enter your address.'})

        try:
            total_amount = service_obj.price if (service_obj.price and service_obj.price > 0) else 0.00

            # Booking Object तयार करा
            booking = us.DirectServiceBooking.objects.create(
                customer=customer,
                service=service_obj,
                provider_email=service_obj.provider_email,
                booking_date=booking_date,
                time_slot=time_slot,
                customer_address=customer_address,
                notes=notes,
                problem_photo=problem_photo,
                payment_mode=payment_mode,
                total_amount=total_amount,
                status='pending',
                payment_status='pending'
            )

            # 🔔 १. Service Provider ला Notification पाठवणे
            try:
                provider_obj = us.ServiceProvider.objects.filter(email=service_obj.provider_email).first()
                if provider_obj:
                    from service_provider.models import ProviderNotification
                    ProviderNotification.objects.create(
                        provider=provider_obj,
                        title=f"New Direct Booking Request! (#{booking.id})",
                        message=f"Customer {customer.full_name} ({customer.mobile}) has booked your service '{service_obj.service_name}' for {booking_date} ({time_slot}). Address: {customer_address}."
                    )
            except Exception as e_pnotif:
                print("Provider Notification Error (Non-Fatal):", e_pnotif)

            # 🔔 २. Customer ला Notification पाठवणे
            try:
                from customer.models import CustomerNotification
                CustomerNotification.objects.create(
                    customer=customer,
                    title="Booking Request Sent!",
                    message=f"Your booking request #{booking.id} for '{service_obj.service_name}' has been sent to provider {provider_obj.full_name if provider_obj else ''}. Please wait for the provider to Accept or Reject."
                )
            except Exception as e_cnotif:
                print("Customer Notification Error (Non-Fatal):", e_cnotif)

            return JsonResponse({
                'success': True,
                'is_cash': True,
                'message': f'🎉 Booking Request Sent! The service provider will review and Accept or Reject your request shortly.',
                'booking_id': booking.id
            })

        except Exception as e_book:
            print("Direct Booking Creation Error:", e_book)
            return JsonResponse({'success': False, 'message': f'Booking could not be saved: {str(e_book)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def verify_booking_payment(request):
    """२. ऑनलाईन पेमेंट पूर्ण झाल्यावर Signature व्हॅलिडेट करणे"""
    if request.method == "POST":
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        booking_id = request.POST.get('booking_id')

        booking = get_object_or_404(us.DirectServiceBooking, id=booking_id)

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            booking.payment_status = 'paid'
            booking.status = 'accepted'
            booking.razorpay_payment_id = razorpay_payment_id
            booking.razorpay_signature = razorpay_signature
            booking.save()

            # 🔔 Provider ला Notification पाठवणे
            provider_obj = us.ServiceProvider.objects.filter(email=booking.provider_email).first()
            if provider_obj:
                from service_provider.models import ProviderNotification
                ProviderNotification.objects.create(
                    provider=provider_obj,
                    title=f"💰 Online Payment Received: ₹{booking.total_amount}!",
                    message=f"Customer {booking.customer.full_name} paid ₹{booking.total_amount} online for Booking #{booking.id} ('{booking.service.service_name}') via Razorpay (Payment ID: {razorpay_payment_id})."
                )

            # 🔔 Customer ला Notification पाठवणे
            from customer.models import CustomerNotification
            CustomerNotification.objects.create(
                customer=booking.customer,
                title="Online Payment Successful! 💳",
                message=f"Your online payment of ₹{booking.total_amount} for Booking #{booking.id} ('{booking.service.service_name}') was successful via Razorpay (Payment ID: {razorpay_payment_id})."
            )

            return JsonResponse({
                'success': True, 
                'message': f'🎉 Online Payment Successful! (Booking #{booking.id} Confirmed)'
            })
        except razorpay.errors.SignatureVerificationError:
            booking.payment_status = 'failed'
            booking.save()
            return JsonResponse({'success': False, 'message': '⚠️ Razorpay verification failed.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})




def contact(req):
    return render(req,'user/contact.html')

