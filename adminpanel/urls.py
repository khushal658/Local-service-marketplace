from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/',views.index,name='admin_dashboard'),
    path('service-categories/',views.service_categories,name='service_categories'),
    path('save-category/',views.save_category,name='save_category'),
    path('save-subcategory/',views.save_subcategory,name='save_subcategory'),

    # category list
    path('categories-list/',views.categories_list,name='categories_list'),
    path('category-status-toggle/<uuid:category_id>/',views.category_status_toggle, name='category_status_toggle'),
    path('update-category/<uuid:category_id>/',views.update_category, name='update_category'),
    path('delete-category/<uuid:category_id>/', views.delete_category, name='delete_category'),

    # subcategory list

    path('subcategories-list/', views.subcategories_list, name='subcategories_list'),
    path('subcategory-status-toggle/<uuid:subcat_id>/', views.subcategory_status_toggle, name='subcategory_status_toggle'),
    path('update-subcategory/<uuid:subcat_id>/', views.update_subcategory, name='update_subcategory'),
    path('delete-subcategory/<uuid:subcat_id>/', views.delete_subcategory, name='delete_subcategory'),

    # service provider approvals
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('approve-provider/<int:provider_id>/', views.approve_provider, name='approve_provider'),
    path('reject-provider/<int:provider_id>/', views.reject_provider, name='reject_provider'),

    # cusotmer list 
    path('customers-list/', views.admin_customers_list, name='admin_customers_list'),
    path('export-customers-csv/', views.export_customers_csv, name='export_customers_csv'),   

    # customer job audit list job post
    path('job-audit-list/', views.admin_job_audit_list, name='admin_job_audit_list'),
    path('earnings-payouts/', views.admin_earnings_payouts, name='admin_earnings_payouts'),

    # cusotmer direct booking 
    path('direct-bookings/',views.cusotmer_direct_bookings, name='admin_direct_bookings'),
]