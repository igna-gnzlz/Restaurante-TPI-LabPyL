# Generated by Django 5.2 on 2025-06-11 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings_app', '0003_remove_booking_date_time_remove_table_booking_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='table',
            name='number',
            field=models.IntegerField(default=0, unique=True),
        ),
    ]
