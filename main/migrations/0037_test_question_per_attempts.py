# Generated by Django 5.2 on 2025-06-17 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_test_max_tries'),
    ]

    operations = [
        migrations.AddField(
            model_name='test',
            name='question_per_attempts',
            field=models.IntegerField(default=10, null=True),
        ),
    ]
