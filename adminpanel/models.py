from django.db import models
import uuid

# Create your models here.

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    icon_class = models.CharField(max_length=100)
    providers_count = models.CharField(max_length=100)
    trend_badge = models.CharField(max_length=100, blank=True)
    category_image = models.ImageField(upload_to='category_images/')
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    subcat_names = models.CharField(max_length=100)
    subcat_icons = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.subcat_names

class AdminNotification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Admin Notif: {self.title}"
