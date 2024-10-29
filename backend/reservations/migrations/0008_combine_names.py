# Generated by Django 4.1.1 on 2023-11-02 06:27

from django.db import migrations, models

def merge_names(apps, _schema_editor):
    Room = apps.get_model('reservations', 'Room')
    for room in Room.objects.all():
        names = [room.primary]
        for name in room.secondary.split(','):
            names.append(name)

        names.sort()
        room.names = ','.join(names)
        room.save()

class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0007_swap'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='names',
            field=models.CharField(max_length=50,
                                   verbose_name='Names',
                                   null=True,
                                   blank=True)
        ),
        migrations.RunPython(merge_names),
        migrations.RemoveField(
            model_name='room',
            name='primary'),
        migrations.RemoveField(
            model_name='room',
            name='secondary'),
        migrations.RemoveField(
            model_name='room',
            name='is_special'),
        migrations.RemoveField(
            model_name='guest',
            name='hotel'),
        migrations.RemoveField(
            model_name='guest',
            name='room_number'),
        migrations.RemoveField(
            model_name='room',
            name='placed_by_roombot')
    ]
