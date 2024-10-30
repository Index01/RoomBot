from django.core.checks import Error, Warning, Info, register
from reservations.models import Room, Guest

@register(deploy=True)
def guest_drama_check(app_configs, **kwargs):
    errors = []
    guests = Guest.objects.all()
    for guest in guests:
        if guest.jwt == '' and guest.can_login:
            errors.append(Error(f"Guest {guest.email} has an empty jwt field!"))

        if guest.ticket and Guest.objects.filter(ticket = guest.ticket).count() > 1:
            errors.append(Error(f"Guest {guest.email} has multiple tickets assocaited with it!"))

    multi_room_guests = [','.join(x.room_set.all()) for x in Guest.objects.all() if x.room_set.count() > 1]
    if len(multi_room_guests) > 0:
        errors.append(Error(f"Guests have has multiple rooms {multi_room_guests}"))


    return errors

@register(deploy=True)
def room_drama_check(app_configs, **kwargs):
    errors = []
    rooms = Room.objects.all()
    for room in rooms:
        if room.guest and room.number != room.guest.room_number:
            errors.append(Error(f"Room/guest number mismatch {room.number} / {room.guest.room_number}",
                                hint='Manually reconcile room/guest numbers'))

        if room.guest and room.primary != room.guest.name:
            errors.append(Error(f"Room/guest name mismatch {room.primary} / {room.guest.name}",
                                hint='Manually reconcile room/guest names'))

        # side effect of transferring placed rooms
        if room.sp_ticket_id:
            guest = None
            alt_msg = ''
            try:
                guest = Guest.objects.get(ticket=room.sp_ticket_id)
                if room.number != guest.room_number:
                    errors.append(Error(f"Ticket {room.sp_ticket_id} room/guest number mismatch {room.number} / {guest.room_number}",
                                        hint='Manually reconcile room/guest numbers for specified ticket'))

                if room.primary != guest.name:
                    errors.append(Error(f"Ticket {room.sp_ticket_id} room/guest name mismatch {room.primary} / {guest.name}",
                                        hint='Manually reconcile room/guest names for specified ticket'))

            except Guest.DoesNotExist:
                errors.append(Error(f"Original owner for ticket {room.sp_ticket_id} not found",
                                    hint='Good luck, I guess?'))

            if room.guest is None:
                errors.append(Error(f"Room {room.number} ({room.name_hotel}) sp_ticket_id {room.sp_ticket_id} missing guest",
                                    hint='Manually reconcile w/ sources of truth'))

            if room.guest is not None and room.number != guest.room_number \
               and room.primary != guest.name \
                   and guest is not None:
                try:
                    guest = Guest.objects.get(transfer=room.sp_ticket_id)
                    if room.number != guest.room_number:
                        errors.append(Error(f"Ticket {room.sp_ticket_id} transfer {guest.ticket} room/guest number mismatch {room.number} / {guest.room_number}",
                                            hint='Manually reconcile room/guest numbers for specified ticket(s)'))

                    if room.primary != guest.name:
                        errors.append(Error(f"Ticket {room.sp_ticket_id} transfer {guest.ticket} room/guest name mismatch {room.primary} / {guest.name}",
                                            hint='Manually reconcile room/guest names for specified ticket(s)'))

                except Guest.DoesNotExist:
                    errors.append(Error(f"Ticket {room.sp_ticket_id} transfer owner not found",
                                  hint='Good luck, I guess?'))

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

