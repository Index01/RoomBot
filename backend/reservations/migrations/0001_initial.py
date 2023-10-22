# Generated by Django 4.1.1 on 2023-10-12 23:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Guest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=240, verbose_name='Name')),
                ('email', models.EmailField(max_length=254)),
                ('ticket', models.CharField(max_length=20, verbose_name='Ticket')),
                ('invitation', models.CharField(max_length=20, verbose_name='Invitation')),
                ('jwt', models.CharField(max_length=240, verbose_name='JWT')),
                ('room_number', models.CharField(max_length=20, verbose_name='RoomNumber', blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=240, verbose_name='Name')),
                ('email', models.EmailField(max_length=254)),
                ('is_admin', models.BooleanField(default=False, verbose_name='Admin')),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reservations.guest')),
            ],
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=20, verbose_name='Number')),
                ('name_take3', models.CharField(max_length=50, verbose_name='Take3Name')),
                ('name_hotel', models.CharField(max_length=50, verbose_name='HotelName')),
                ('is_available', models.BooleanField(default=False, verbose_name='Available')),
                ('is_swappable', models.BooleanField(default=False, verbose_name='IsSwappable')),
                ('is_smoking', models.BooleanField(default=False, verbose_name='SmokingRoom')),
                ('is_lakeview', models.BooleanField(default=False, verbose_name='LakeviewRoom')),
                ('is_ada', models.BooleanField(default=False, verbose_name='ADA')),
                ('is_hearing_accessible', models.BooleanField(default=False, verbose_name='HearingAccessible')),
                ('is_art', models.BooleanField(default=False, verbose_name='ArtRoom')),
                ('is_special', models.BooleanField(default=False, verbose_name='SpecialRoom')),
                ('is_comp', models.BooleanField(default=False, verbose_name='CompRoom')),
                ('is_placed', models.BooleanField(default=False, verbose_name='PlacedRoom')),
                ('swap_code', models.CharField(blank=True, max_length=200, null=True, verbose_name='SwapCode')),
                ('swap_time', models.DateTimeField(blank=True, null=True)),
                ('check_in', models.DateField(blank=True, null=True)),
                ('check_out', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, verbose_name='RoomNotes')),
                ('guest_notes', models.TextField(blank=True, verbose_name='GuestNotes')),
                ('sp_ticket_id', models.CharField(max_length=20, verbose_name='SecretPartyTicketID', blank=True, null=True)),
                ('primary', models.CharField(max_length=50, verbose_name='PrimaryContact')),
                ('secondary', models.CharField(max_length=50, verbose_name='SecondaryContact')),
                ('placed_by_roombot', models.BooleanField(default=False, verbose_name='PlacedByRoombot')),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reservations.guest')),
            ],
        ),
    ]
