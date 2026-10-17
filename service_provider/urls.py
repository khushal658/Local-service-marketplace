from django.urls import path
from . import views

urlpatterns = [
    # path('dashboard/', views.index, name='dashboard_provider'),
    path("dashboard/",views.provider_dashboard, name="provider_dashboard"),
    path("provider/logout/", views.provider_logout, name="provider_logout"),

    path('update_profile/',views.provider_profile_update, name="provider_profile_update"),

    # add new service
    path('add-service/',views.add_service, name="add_service"),
    path('get-subcategories/', views.get_subcategories_by_category, name='get_subcategories_by_category'),

    # service list
    path('my-services/',views.my_services_list, name="my_services"),
    path('edit-service/<uuid:service_id>/', views.edit_service, name='edit_service'),
    path('toggle-service-status/<uuid:service_id>/', views.toggle_service_status, name='toggle_service_status'),
    path('delete-service/<uuid:service_id>/', views.delete_service, name='delete_service'),


    # direct customer booking requests for posted services
    path('booking-requests/', views.provider_booking_requests, name='provider_booking_requests'),
    path('accept-booking/<int:booking_id>/', views.accept_booking_request, name='accept_booking_request'),
    path('reject-booking/<int:booking_id>/', views.reject_booking_request, name='reject_booking_request'),
    path('my-bookings/', views.provider_my_bookings, name='provider_my_bookings'),
    path('complete-direct-booking/<int:booking_id>/', views.complete_direct_booking, name='complete_direct_booking'),

    # customer job leads for service provider
    path('job-leads/', views.provider_job_leads, name='provider_job_leads'),
    path('submit-quote/', views.submit_service_quote, name='submit_service_quote'),
    path('accepted-jobs/', views.provider_accepted_jobs, name='provider_accepted_jobs'),
    path('start-job/<int:quote_id>/', views.start_provider_job, name='start_provider_job'),
    path('complete-job/<int:quote_id>/', views.complete_provider_job, name='complete_provider_job'),
    path('earnings/', views.provider_earnings, name='provider_earnings'),
    path('download-receipt/<int:quote_id>/', views.download_receipt, name='provider_download_receipt'),
    path('mark-notifications-read/', views.mark_provider_notifications_read, name='mark_provider_notifications_read'),
]