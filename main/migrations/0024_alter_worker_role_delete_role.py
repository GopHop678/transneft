# Generated by Django 5.2 on 2025-05-25 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_alter_uploadedfile_file_type_delete_filetype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='role',
            field=models.CharField(choices=[('admin', 'Администратор'), ('curator', 'Куратор'), ('worker', 'Сотрудник')]),
        ),
        migrations.DeleteModel(
            name='Role',
        ),
    ]
