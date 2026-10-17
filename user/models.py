from django.db import models
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.



class ServiceProvider(models.Model):
    EXPERIENCE_CHOICES = [
        ('0-1', 'Fresh / Less than 1 year'),
        ('1-3', '1 - 3 Years'),
        ('3-5', '3 - 5 Years'),
        ('5+', '5+ Years'),
    ]

    CATEGORY_CHOICES = [
        ('electrician', 'Electrician'),
        ('plumber', 'Plumber'),
        ('carpenter', 'Carpenter'),
        ('painter', 'Painter'),
        ('ac_tech', 'AC Technician'),
        ('cleaner', 'Cleaner'),
        ('beautician', 'Beautician'),
        ('appliance', 'Appliance Repair'),
        ('cctv', 'CCTV Technician'),
        ('other', 'Other Category'),
    ]

    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, blank=True, null=True)
   
    full_name = models.CharField(max_length=150)

    business_name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    # New Subcategory field
   
    other_category = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    mobile = models.CharField(
        max_length=10,
        unique=True
    )

    profile_image = models.ImageField(
    upload_to="provider_profiles/",
    blank=True,
    null=True
         )

    city_area = models.CharField(max_length=200)

    pincode = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    experience = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_approved = models.BooleanField(default=False)

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return self.full_name

    def get_avg_rating(self):
        from customer.models import ProviderReview
        from django.db.models import Avg
        reviews = ProviderReview.objects.filter(provider=self)
        if reviews.exists():
            avg = reviews.aggregate(Avg('rating'))['rating__avg']
            return round(avg, 1) if avg else 0.0
        return 0.0

    def get_review_count(self):
        from customer.models import ProviderReview
        return ProviderReview.objects.filter(provider=self).count()


class ProviderRegistrationOTP(models.Model):

    email = models.EmailField(unique=True)

    otp = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


# 1. Customer Profile Model
class CustomerRegistration(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile', blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    full_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=10, unique=True)
    profile_photo = models.ImageField(upload_to='customer_photos/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.full_name} ({self.email})"


    
# 2. Email OTP Storage Model
class EmailOTP(models.Model):
    email = models.EmailField(unique=True)
    
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    def is_valid(self):
        # OTP 5 मिनिटांसाठी वैध राहील
        return timezone.now() < self.created_at + datetime.timedelta(minutes=5)
    def __str__(self):
        return f"{self.email} - {self.otp}"




# cusotmer service booking model

class DirectServiceBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_MODE_CHOICES = (
        ('cash', 'Cash on Service'),
        ('online', 'Online Payment (Razorpay/UPI)'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )

    customer = models.ForeignKey(CustomerRegistration, on_delete=models.CASCADE, related_name='direct_bookings')
    service = models.ForeignKey('service_provider.AddService', on_delete=models.CASCADE, related_name='direct_service_bookings')
    provider_email = models.EmailField()
    
    # 1. Customer Booking Form Details
    booking_date = models.CharField(max_length=50) # e.g. "Today", "Tomorrow"
    time_slot = models.CharField(max_length=50)   # e.g. "11:00 – 13:00"
    customer_address = models.TextField()
    latitude = models.CharField(max_length=50, blank=True, null=True)   # GPS Coordinates
    longitude = models.CharField(max_length=50, blank=True, null=True)  # GPS Coordinates
    notes = models.TextField(blank=True, null=True)                      # Special Instructions
    problem_photo = models.ImageField(upload_to='booking_photos/', blank=True, null=True) # Image
    
    # 2. Payment Gateway Fields (Razorpay / Cash)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Razorpay Details
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.service.service_name} ({self.payment_mode} - {self.payment_status})"
