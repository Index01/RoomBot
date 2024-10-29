from django.core.checks import Error, Warning, Info, register
from reservations.models import Room, Guest

@register(deploy=True)
def guest_drama_check(app_configs, **kwargs):
    errors = []
    guests = Guest.objects.all()
    for guest in guests:
        if guest.jwt == '' and guest.can_login:
            errors.append(Error(f"Guest {guest.email} has an empty jwt field!",
                                hint='Indicative of guest import bug. Will require manual reconciliation.',
                                obj=guest))

        if guest.transfer:
            try:
                Guest.objects.get(ticket=guest.transfer)
            except Guest.DoesNotExist:
                errors.append(Error(f"Guest {guest.email} a transfer ({guest.transfer}) that we cannot find",
                                    hint='Indicative of guest import bug. Will require manual reconciliation.',
                                    obj=guest))

    for guest_email in Guest.objects.values('email').distinct():
        for guest in Guest.objects.filter(email=guest_email):
            guest_jwt = set([x.jwt for x in guest])
            if len(guest_jwt) > 1:
                errors.append(Error(f"Guest {guest.email} has {len(guest_jwt)} distinct jwt entries!",
                                    hint='Indicative of guest import bug. Will require manual reconciliation.',
                                    obj=guest))

    return errors

@register(deploy=True)
def room_drama_check(app_configs, **kwargs):
    errors = []
    rooms = Room.objects.all()
    for room in rooms:
        if room.guest and \
           not room.resident(room.guest):
            errors.append(Error(f"Room/guest name mismatch {room.names} / {room.guest}",
                                hint='Manually reconcile room/guest names',
                                obj=room))

        # side effect of transferring placed rooms
        if room.sp_ticket_id and room.guest:
            guest = None
            try:
                guest = Guest.objects.get(ticket=room.sp_ticket_id)
                if room.guest != guest:
                    errors.append(Error(f"Ticket {room.sp_ticket_id} guest mismatch {room.guest} / {guest}",
                                        hint='Manually reconcile guest entries. Good luck.',
                                        obj=room))

                if room.guest and not room.resident(room.guest):
                    errors.append(Error(f"Ticket {room.sp_ticket_id} guest {room.guest.name} not found among {room.names}",
                                        hint='Manually reconcile room/guest names for specified ticket',
                                        obj=room))

            except Guest.DoesNotExist:
                errors.append(Warning(f"No guest record for ticket {room.sp_ticket_id} found",
                                    hint='Has guest list been imported? Reconcile with source(s) of truth.',
                                    obj=room))

        elif room.sp_ticket_id and not room.guest:
            errors.append(Warning(f"Ticket {room.sp_ticket_id} without any guest record",
                                hint='Has guest list been imported? Reconcile with source(s) of truth.',
                                obj=room))

        # general corruption which could bubble up during orm/sql manipulation
        if room.check_in is None:
            errors.append(Warning(f"Room {room.name_hotel} {room.number} has blank check_in date",
                                  hint='Fix source of truth for rooms',
                                  obj=room))

        if room.check_out is None:
            errors.append(Warning(f"Room {room.name_hotel} {room.number} has blank check_out date",
                                  hint='Fix source of truth for rooms',
                                  obj=room))


    return errors

