# Generated by Django 5.2 on 2025-05-13 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_alter_result_is_passed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='percentage_to_pass',
            field=models.IntegerField(default=80, null=True),
        ),
        migrations.AlterField(
            model_name='test',
            name='time_limit',
            field=models.IntegerField(default=20, null=True),
        ),
    ]
