# Generated by Django 4.1.1 on 2023-11-09 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_number', models.CharField(max_length=10, unique=True, verbose_name='RoomNumber')),
                ('description', models.CharField(max_length=50, verbose_name='Description')),
            ],
        ),
    ]