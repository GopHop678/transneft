# Generated by Django 5.2 on 2025-05-23 04:54

import main.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_filetype_uploadedfile_file_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='file',
            field=models.FileField(upload_to=main.models.upload_path),
        ),
    ]
