from django.shortcuts import render,redirect
from . import models
from user import models as us
from django.contrib import messages
from django.shortcuts import get_object_or_404
# from customer.models import CustomServiceRequest, ServiceQuote
from customer import models as cs
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv


# Create your views here.

def index(req):
   

    # १. Provider आणि Customer ची संख्या
    total_providers = us.ServiceProvider.objects.count()
    total_customers = us.CustomerRegistration.objects.count()
    total_bookings = cs.CustomServiceRequest.objects.count()

    # २. ॲडमिनला आलेले एकूण १०% पेमेंट
    paid_quotes = cs.ServiceQuote.objects.filter(payment_status='paid')
    total_admin_payment = sum(
        (float(q.final_amount) if q.final_amount else float(q.quoted_price)) * 0.10
        for q in paid_quotes
    )

    context = {
        'total_providers': total_providers,
        'total_customers': total_customers,
        'total_bookings': total_bookings,
        'total_admin_payment': round(total_admin_payment, 2),
    }
    return render(req, 'admin/index.html', context)

def service_categories(req):
    all_categories = models.Category.objects.all()
    return render(req,'admin/service_categories.html', {'all_categories': all_categories})

def save_category(req):
    if req.method == 'POST':
         category_image = req.FILES.get('category_image')
    
    # 1. डेटाबेसमध्ये सेव्ह करण्याच्या आधी 2 MB चे चेक करा:
         if category_image:
                # 🛑 1. जर फोटो सेलेक्टच केला नसेल तर एरर दाखवा:
                if not category_image:
                    messages.error(req, "❌ Please select an image file!", extra_tags='image_error')
                    return redirect('service_categories')

                
                # 🛑 2. जर फोटोव्यतिरिक्त इतर काहीही (PDF, Video, Doc, ZIP) सेलेक्ट केले तर एरर दाखवा:
                if not category_image.content_type.startswith('image/'):
                    messages.error(req, "❌ Only image files (JPG, PNG, WEBP) are allowed!", extra_tags='image_error')
                    return redirect('service_categories')
                
                max_size = 2 * 1024 * 1024  # 2MB in bytes    
                if category_image.size > max_size:
                    messages.error(req, "Image size exceeds the maximum limit of 2MB.", extra_tags='image_error')
                    return redirect('service_categories')
                
    models.Category.objects.create(
            name = req.POST.get('name'),
            starting_price = req.POST.get('starting_price'),
            icon_class = req.POST.get('icon_class'),
            providers_count = req.POST.get('providers_count'),
            trend_badge = req.POST.get('trend_badge'),
            category_image = category_image,
            description = req.POST.get('description')
        )
    messages.success(req, "Category added successfully! 🎉", extra_tags='category_success')
       
    return redirect('service_categories')



def categories_list(req):
    categories = models.Category.objects.all()
    obj = {
        'categories': categories
    }
    return render(req,'admin/categories_list.html',obj)

def category_status_toggle(req, category_id):
    category = get_object_or_404(models.Category, id=category_id)

    category.is_active = not category.is_active
    category.save()

    if category.is_active:
        messages.success(req, f"'{category.name}' category has been activated successfully! 🟢", extra_tags='status_toggle')
    else:
        messages.warning(req, f"'{category.name}' category is now set to Inactive! 🔴", extra_tags='status_toggle')
    
    return redirect('categories_list')

import os
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from . import models

def update_category(req, category_id):
    category = get_object_or_404(models.Category, id=category_id)

    if req.method == 'POST': 
        new_image = req.FILES.get('category_image')
        if new_image:

            # 🛑 १. जर फोटोव्यतिरिक्त इतर फाईल (PDF, Video, ZIP) निवडली तर एरर दाखवा:
            if not new_image.content_type.startswith('image/'):
                messages.error(req, "❌ Only image files (JPG, PNG, WEBP) are allowed!", extra_tags='image_error')
                return redirect('update_category', category_id=category.id)  
            
            # 🛑 २. जर फोटोची साईझ 2MB पेक्षा जास्त असेल तर एरर दाखवा:
            max_size = 2 * 1024 * 1024  # 2MB in bytes
            if new_image.size > max_size:
                messages.error(req, "❌ Image size exceeds the maximum limit of 2MB!", extra_tags='image_error')
                return redirect('update_category', category_id=category.id)
            
            # 🗑️ ३. नवीन फोटो सेव्ह करण्यापूर्वी जुना फोटो मीडिया फोल्डरमधून डिलीट करा:
            if category.category_image and os.path.isfile(category.category_image.path):
                os.remove(category.category_image.path)

            # व्हॅलिडेशन पास झाल्यास नवीन फोटो सेट करा
            category.category_image = new_image
            
        category.name = req.POST.get('name')
        category.starting_price = req.POST.get('starting_price')
        category.icon_class = req.POST.get('icon_class')
        category.providers_count = req.POST.get('providers_count')
        category.trend_badge = req.POST.get('trend_badge')
        category.description = req.POST.get('description')

        # ४. बदल सेव्ह करा
        category.save()
        messages.success(req, "Category updated successfully! 🎉", extra_tags='update_success')
        return redirect('categories_list') 
        
    return render(req, "admin/update_categorie.html", {'category': category})


def delete_category(req, category_id):
    category = get_object_or_404(models.Category, id=category_id)
    category_name = category.name

    # 🗑️ कॅटेगिरी डेटाबेस मधून डिलीट करण्यापूर्वी फोल्डरमधील फोटो डिलीट करा:
    if category.category_image and os.path.isfile(category.category_image.path):
        os.remove(category.category_image.path)

    category.delete()
    messages.success(req, f"Category '{category_name}' deleted successfully! 🗑️", extra_tags='delete_success')
    return redirect('categories_list')


# subcategory curd start here 


def save_subcategory(req):
    if req.method == 'POST':
        category_id = req.POST.get('category_id')
        category_obj = models.Category.objects.get(id=category_id)
        
        # 1. ॲडमिनने भरलेली सर्व सब-कॅटेगरीजची नावे आणि आयकॉन्स मिळवा (getlist)
        names_list = req.POST.getlist('subcat_names')
        icons_list = req.POST.getlist('subcat_icons')
        
        # 2. zip() लूप वापरून एकाच वेळी सर्व सब-कॅटेगरीज सेव्ह करा
        for name, icon in zip(names_list, icons_list):
            if name.strip():  # खाली सोडलेली नावे टाळणे
                models.SubCategory.objects.create(
                    category = category_obj,
                    subcat_names = name.strip(),
                    subcat_icons = icon.strip() if icon.strip() else 'bi-box-seam-fill'
                )
        
        messages.success(req, "All subcategories added successfully! 🎉", extra_tags='subcategory_success')
        return redirect('service_categories')

def subcategories_list(req):
    subcategories = models.SubCategory.objects.select_related('category').all()
    return render(req, 'admin/subcategories_list.html', {'subcategories': subcategories})


def subcategory_status_toggle(req, subcat_id):
    subcat = get_object_or_404(models.SubCategory, id=subcat_id)
    subcat.is_active = not subcat.is_active
    subcat.save()
    if subcat.is_active:
        messages.success(req, f"'{subcat.subcat_names}' is now Active! 🟢", extra_tags='status_toggle')
    else:
        messages.warning(req, f"'{subcat.subcat_names}' is now Inactive! 🔴", extra_tags='status_toggle')
    return redirect('subcategories_list')




# 3. Update Subcategory View
def update_subcategory(req, subcat_id):
    subcat = get_object_or_404(models.SubCategory, id=subcat_id)
    all_categories = models.Category.objects.all()
    if req.method == 'POST':
        category_id = req.POST.get('category_id')
        subcat.category = get_object_or_404(models.Category, id=category_id)
        subcat.subcat_names = req.POST.get('subcat_name')
        subcat.subcat_icons = req.POST.get('subcat_icon')
        subcat.save()
        messages.success(req, f"Subcategory '{subcat.subcat_names}' updated successfully! 🎉", extra_tags='update_success')
        return redirect('subcategories_list')
    return render(req, 'admin/update_subcategory.html', {'subcat': subcat, 'all_categories': all_categories})

def delete_subcategory(req, subcat_id):
    subcat = get_object_or_404(models.SubCategory, id=subcat_id)
    subcat.delete()
    messages.success(req, f"Subcategory '{subcat.subcat_names}' deleted successfully! 🗑️", extra_tags='delete_success')
    return redirect('subcategories_list')



# -----------------------------
# SERVICE PROVIDER PENDING APPROVALS
# -----------------------------

def pending_approvals(req):
    status_filter = req.GET.get('status', 'pending')
    
    if status_filter == 'approved':
        providers = us.ServiceProvider.objects.filter(approval_status='approved').order_by('-created_at')
    elif status_filter == 'rejected':
        providers = us.ServiceProvider.objects.filter(approval_status='rejected').order_by('-created_at')
    elif status_filter == 'all':
        providers = us.ServiceProvider.objects.all().order_by('-created_at')
    else:
        providers = us.ServiceProvider.objects.filter(approval_status='pending').order_by('-created_at')
        status_filter = 'pending'

    counts = {
        'pending': us.ServiceProvider.objects.filter(approval_status='pending').count(),
        'approved': us.ServiceProvider.objects.filter(approval_status='approved').count(),
        'rejected': us.ServiceProvider.objects.filter(approval_status='rejected').count(),
        'all': us.ServiceProvider.objects.count()
    }

    context = {
        'providers': providers,
        'selected_status': status_filter,
        'counts': counts
    }
    return render(req, 'admin/pending_approvals.html', context)

def approve_provider(req, provider_id):
    provider = get_object_or_404(us.ServiceProvider, id=provider_id)
    provider.is_approved = True
    provider.approval_status = 'approved'
    provider.save()
    messages.success(req, f"Service Provider '{provider.full_name}' has been approved successfully! 🎉", extra_tags='approval_success')
    return redirect('pending_approvals')

def reject_provider(req, provider_id):
    provider = get_object_or_404(us.ServiceProvider, id=provider_id)
    provider.is_approved = False
    provider.approval_status = 'rejected'
    provider.save()
    messages.warning(req, f"Service Provider '{provider.full_name}' registration request has been rejected.", extra_tags='approval_reject')
    return redirect('pending_approvals')


# cusotmer list 



def admin_customers_list(req):
    """१. ॲडमिनसाठी सर्व ग्राहकांची (Customers) यादी व शोध (Search) दाखवणे"""
    search_query = req.GET.get('search', '').strip()
    
    customers_list = us.CustomerRegistration.objects.all().order_by('-created_at')
    
    # शोध घ्या (Name, Email, Mobile किंवा City ने शोधणे)
    if search_query:
        from django.db.models import Q
        customers_list = customers_list.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(mobile__icontains=search_query) |
            Q(city__icontains=search_query)
        )

    # एकूण ग्राहकांची संख्या
    total_customers_count = customers_list.count()

    # Pagination: एका पानावरील १० ग्राहक
    paginator = Paginator(customers_list, 15)
    page_number = req.GET.get('page')
    customers = paginator.get_page(page_number)

    context = {
        'customers': customers,
        'total_customers_count': total_customers_count,
        'search_query': search_query,
    }
    return render(req, 'admin/customers_list.html', context)


def export_customers_csv(req):
    """२. सर्व Customers चा डेटा Excel/CSV फाईल स्वरूपात डाऊनलोड करणे"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="registered_customers_list.csv"'

    writer = csv.writer(response)
    # CSV Header Row (कॉलम्सची नावे)
    writer.writerow(['SR NO', 'Full Name', 'Email Address', 'Mobile Number', 'City', 'State', 'Pincode', 'Address', 'Registration Date'])

    customers = us.CustomerRegistration.objects.all().order_by('-created_at')
    
    for idx, customer in enumerate(customers, start=1):
        writer.writerow([
            idx,
            customer.full_name,
            customer.email or '',
            customer.mobile,
            customer.city or '',
            customer.state or '',
            customer.pincode or '',
            customer.address or '',
            customer.created_at.strftime('%d-%m-%Y %I:%M %p') if customer.created_at else ''
        ])

    return response




#  cusotmer  working posted start here 


def admin_job_audit_list(req):
    """१. ॲडमिनसाठी सर्व कस्टमर पोस्ट केलेले जॉब्स, Bids, पेमेंट व १०% कमिशन ट्रॅकिंग"""
    from customer import models as cs
    from django.core.paginator import Paginator

    job_requests_list = cs.CustomServiceRequest.objects.select_related('customer').prefetch_related('quotes', 'quotes__provider').order_by('-created_at')

    # एकूण कमाईची आकडेमोड (Summary Calculation)
    total_revenue = 0.0
    total_admin_commission = 0.0
    total_provider_payout = 0.0

    completed_paid_quotes = cs.ServiceQuote.objects.filter(payment_status='paid')
    for q in completed_paid_quotes:
        amt = q.total_paid_amount
        total_revenue += amt
        total_admin_commission += (amt * 0.10)
        total_provider_payout += (amt * 0.90)

    # Pagination: 10 items per page
    paginator = Paginator(job_requests_list, 10)
    page_number = req.GET.get('page')
    job_requests = paginator.get_page(page_number)

    context = {
        'job_requests': job_requests,
        'total_revenue': round(total_revenue, 2),
        'total_admin_commission': round(total_admin_commission, 2),
        'total_provider_payout': round(total_provider_payout, 2),
    }
    return render(req, 'admin/job_audit_list.html', context)




# cusotmer direct booking start here
def cusotmer_direct_bookings(req):

    return render(req, 'admin/direct_bookings.html')    




def admin_earnings_payouts(req):
    """३. ॲडमिनसाठी Earnings & Payouts ट्रॅकिंग (कोणत्या ग्राहकाकडून किती पेमेंट आले व १०% नफा)"""
    from customer import models as cs
    from django.core.paginator import Paginator

    paid_quotes_list = cs.ServiceQuote.objects.filter(payment_status='paid').select_related('request', 'request__customer', 'provider').order_by('-created_at')

    total_revenue = 0.0
    total_admin_commission = 0.0
    total_provider_payout = 0.0

    for q in paid_quotes_list:
        amt = q.total_paid_amount
        q.calc_admin_commission = q.admin_commission
        q.calc_provider_share = q.provider_share
        total_revenue += amt
        total_admin_commission += q.calc_admin_commission
        total_provider_payout += q.calc_provider_share

    paginator = Paginator(paid_quotes_list, 15)
    page_number = req.GET.get('page')
    paid_quotes = paginator.get_page(page_number)

    context = {
        'paid_quotes': paid_quotes,
        'total_revenue': round(total_revenue, 2),
        'total_admin_commission': round(total_admin_commission, 2),
        'total_provider_payout': round(total_provider_payout, 2),
    }
    return render(req, 'admin/earnings_payouts.html', context)
