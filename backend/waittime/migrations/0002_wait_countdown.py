# Generated by Django 4.1.1 on 2023-11-09 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waittime', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wait',
            name='countdown',
            field=models.BooleanField(default=False, verbose_name='CountDown'),
        ),
        migrations.AddField(
            model_name='wait',
            name='free_update',
            field=models.BooleanField(default=False, verbose_name='FreeUpdate'),
        ),

    ]
