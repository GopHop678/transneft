# Generated by Django 5.2 on 2025-05-22 14:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_rename_file_path_uploadedfile_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uploadedfile',
            name='file_type',
        ),
        migrations.DeleteModel(
            name='FileType',
        ),
    ]
