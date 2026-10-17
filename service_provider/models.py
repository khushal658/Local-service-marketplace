
import uuid
from django.db import models
from adminpanel.models import Category, SubCategory

class AddService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Provider Connection (लॉगिन असणाऱ्या प्रोव्हायडरशी जोडणे)
    provider_email = models.EmailField() # किंवा ForeignKey to ServiceProvider
    
    service_name = models.CharField(max_length=150)
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='provider_services')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='provider_services', null=True, blank=True)
    
    service_description = models.TextField()
    
    service_image = models.ImageField(upload_to='service_images/', null=True, blank=True) # Main Image (Step 1)
    
    # Media Uploads (Step 4 - 3 Extra Images & 2 Videos)
    gallery_image1 = models.ImageField(upload_to='service_images/gallery/', null=True, blank=True)
    gallery_image2 = models.ImageField(upload_to='service_images/gallery/', null=True, blank=True)
    gallery_image3 = models.ImageField(upload_to='service_images/gallery/', null=True, blank=True)
    
    service_video = models.FileField(upload_to='service_videos/', null=True, blank=True)
    service_video2 = models.FileField(upload_to='service_videos/', null=True, blank=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    
    service_area = models.CharField(max_length=150)
    service_pincode = models.CharField(max_length=255, null=True, blank=True)
    
    experience = models.CharField(max_length=50)
    
    skills_included = models.TextField()
    
    availability = models.CharField(max_length=100, default="9 AM - 7 PM")
    available_days = models.CharField(max_length=255, default="All Days (Mon - Sun)", null=True, blank=True)
    
    contact_number = models.CharField(max_length=15)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} ({self.provider_email})"

from user import models as us

class ProviderNotification(models.Model):
    provider = models.ForeignKey(us.ServiceProvider, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.provider.full_name}"
