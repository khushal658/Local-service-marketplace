from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='user_index'),
    path('service/', views.service, name='service'),
    path('view_service', views.view_service, name="view_service"),
    path('category/', views.category, name="category"),
    path('subcategory/', views.subcategory, name="subcategory"),
    path('become-provider/', views.become_provider, name="become_provider"),
    path('customer-register/', views.customer_register, name="customer_register"),
    path('contact/',views.contact, name="contact"),

    



    # service provider registation

    path("provider/send-otp/",views.send_provider_otp,name="provider_send_otp"),

     path("provider/login/", views.provider_login,name="provider_login"),

    path("provider/verify-otp/",views.verify_provider_otp,name="provider_verify_otp"),

    path("provider/register/",views.provider_register,name="provider_register"),

    # customers registration

    path('customer/register/', views.customer_register, name='customer_register'),
    path('customer/send-otp/', views.send_customer_otp, name='send_customer_otp'),
    path('customer/verify-otp/', views.verify_customer_otp, name='verify_customer_otp'),
    path('login/', views.customer_login, name="login"),
    path('customer/login/', views.customer_login, name="customer_login"),


    # cusotmer service booking model
    path('book-service-api/<str:service_id>/', views.book_service_api, name='book_service_api'),
    path('verify-booking-payment/', views.verify_booking_payment, name='verify_booking_payment'),
    
]
