from django.db import models
from user import models as us

class CustomServiceRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'Work In Progress'),
        ('work_completed', 'Work Completed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    customer = models.ForeignKey(us.CustomerRegistration, on_delete=models.CASCADE, related_name='custom_requests')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    city_area = models.CharField(max_length=150)
    budget = models.CharField(max_length=50, blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.customer.full_name}"
    



# Service Provider Quotation Model (नवीन कोटेशन मॉडेल)
class ServiceQuote(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'Work In Progress'),
        ('work_completed', 'Work Completed'),
        ('rejected', 'Rejected'),
    )

    request = models.ForeignKey(CustomServiceRequest, on_delete=models.CASCADE, related_name='quotes')
    provider = models.ForeignKey(us.ServiceProvider, on_delete=models.CASCADE, related_name='submitted_quotes')
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2)  # प्रोव्हायडरने दिलेली किंमत (₹)
    message = models.TextField(blank=True, null=True)                    # मेसेज/कामाचा तपशील
    estimated_time = models.CharField(max_length=100, blank=True, null=True) # उदा. "२ तासांत"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    extra_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    extra_work_notes = models.TextField(null=True, blank=True)
    payment_mode = models.CharField(max_length=20, choices=[('cash', 'Cash'), ('online', 'Online')], null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)

    
    @property
    def total_paid_amount(self):
        """ग्राहकाने भरलेली एकूण रक्कम (मूळ किंमत + अतिरिक्त चार्ज)"""
        return float(self.final_amount) if self.final_amount else float(self.quoted_price)
    @property
    def admin_commission(self):
        """१०% ॲडमिन कमिशन (10% Admin Share)"""
        return round(self.total_paid_amount * 0.10, 2)
    @property
    def provider_share(self):
        """९०% प्रोव्हायडरचा निव्वळ हिस्सा (90% Provider Net Payout)"""
        return round(self.total_paid_amount * 0.90, 2)

    def __str__(self):
        return f"{self.provider.full_name} - ₹{self.quoted_price} for {self.request.title}"


class CustomerNotification(models.Model):
    customer = models.ForeignKey(us.CustomerRegistration, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.title}"


class ProviderReview(models.Model):
    provider = models.ForeignKey(us.ServiceProvider, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(us.CustomerRegistration, on_delete=models.CASCADE)
    request = models.ForeignKey(CustomServiceRequest, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} -> {self.provider.full_name} ({self.rating}★)"
