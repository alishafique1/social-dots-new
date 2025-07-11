# Generated by Django 4.2.7 on 2025-07-03 17:05

from django.db import migrations, models

def set_default_images(apps, schema_editor):
    Project = apps.get_model('core', 'Project')
    Service = apps.get_model('core', 'Service')
    
    for project in Project.objects.all():
        if not project.image:
            project.image = 'project_images/default.jpg'
            project.save()
            
    for service in Service.objects.all():
        if not service.image:
            service.image = 'service_images/default.jpg'
            service.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_portfolio_content_type'),
    ]

    operations = [
        migrations.RunPython(set_default_images),
        migrations.AlterField(
            model_name='project',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='project_images/'),
        ),
        migrations.AlterField(
            model_name='service',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='service_images/'),
        ),
    ]
