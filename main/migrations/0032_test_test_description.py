# Generated by Django 5.2 on 2025-06-10 03:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0031_rename_first_name_worker_full_name_worker_job_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='test',
            name='test_description',
            field=models.CharField(max_length=1000, null=True),
        ),
    ]
