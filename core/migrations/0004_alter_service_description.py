# Generated by Django 4.2.7 on 2025-06-27 16:57

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_service_service_type_alter_service_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='description',
            field=ckeditor_uploader.fields.RichTextUploadingField(),
        ),
    ]
