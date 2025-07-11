# Generated by Django 4.2.7 on 2025-07-04 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_portfolio_image_alter_project_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='cloudinary_image_id',
            field=models.CharField(blank=True, help_text='Cloudinary public ID for the image', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='portfolio_images/'),
        ),
    ]
