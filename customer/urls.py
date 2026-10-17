from django.urls import path
from . import views

urlpatterns = [
   path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
   path('logout/', views.customer_logout, name='customer_logout'),
   path('profile/', views.customer_profile, name='customer_profile'),
   path('post-custom-request/', views.post_custom_request, name='post_custom_request'),
   path('my-requests/', views.my_requests, name='customer_my_requests'),
   path('direct-bookings/', views.customer_direct_bookings, name='customer_direct_bookings'),
   path('accept-quote/<int:quote_id>/', views.accept_quote, name='accept_quote'),
   path('delete-request/<int:request_id>/', views.delete_custom_request, name='delete_custom_request'),
   path('edit-request/<int:request_id>/', views.edit_custom_request, name='edit_custom_request'),

   # payment-related URLs
   path('create-razorpay-order/<int:quote_id>/', views.create_razorpay_order, name='create_razorpay_order'),
   path('verify-razorpay-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
   path('pay-cash/<int:quote_id>/', views.pay_cash, name='pay_cash'),
   path('payments/', views.customer_payments, name='customer_payments'),
   path('download-receipt/<int:quote_id>/', views.download_receipt, name='download_receipt'),
   path('submit-review/<int:quote_id>/', views.submit_provider_review, name='submit_provider_review'),
   path('mark-notifications-read/', views.mark_customer_notifications_read, name='mark_customer_notifications_read'),
]