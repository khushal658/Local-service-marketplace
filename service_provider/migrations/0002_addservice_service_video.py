from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service_provider', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='AddService',
            name='service_video',
            field=models.FileField(blank=True, null=True, upload_to='service_videos/'),
        ),
    ]
