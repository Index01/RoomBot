# Generated by Django 4.1.1 on 2023-11-06 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Wait',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, verbose_name='WaitName')),
                ('short_name', models.CharField(max_length=20, unique=True, verbose_name='ShortName')),
                ('password', models.CharField(blank=True, max_length=30, null=True, verbose_name='Password')),
                ('time', models.IntegerField(verbose_name='WaitTime'))
            ],
        ),
    ]
