# Generated by Django 5.2 on 2025-05-28 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0025_alter_question_question_type_delete_questiontype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='file_type',
            field=models.CharField(choices=[('img', 'Фото'), ('mp4', 'Видео')]),
        ),
    ]
