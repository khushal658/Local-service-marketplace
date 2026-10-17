from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service_provider', '0002_addservice_service_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='AddService',
            name='gallery_image1',
            field=models.ImageField(blank=True, null=True, upload_to='service_images/gallery/'),
        ),
        migrations.AddField(
            model_name='AddService',
            name='gallery_image2',
            field=models.ImageField(blank=True, null=True, upload_to='service_images/gallery/'),
        ),
        migrations.AddField(
            model_name='AddService',
            name='gallery_image3',
            field=models.ImageField(blank=True, null=True, upload_to='service_images/gallery/'),
        ),
        migrations.AddField(
            model_name='AddService',
            name='service_video2',
            field=models.FileField(blank=True, null=True, upload_to='service_videos/'),
        ),
    ]
