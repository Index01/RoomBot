# Generated by Django 4.1.1 on 2024-10-25 01:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0005_room_swap_code_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='primary',
            field=models.CharField(max_length=200, verbose_name='PrimaryContact'),
        ),
        migrations.AlterField(
            model_name='room',
            name='secondary',
            field=models.CharField(max_length=200, verbose_name='SecondaryContact'),
        ),
    ]