from django.core.checks import Error, Warning, register
from reservations.models import Room, Guest

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

                    errors.append(Error(f"Ticket {room.sp_ticket_id} room/guest name mismatch {room.primary} / {guest.name}",
                                        hint='Manually reconcile room/guest names for specified ticket'))

            except Guest.DoesNotExist:
                errors.append(Error(f"Original owner for ticket {room.sp_ticket_id} not found",
                                    hint='Good luck, I guess?'))

            if room.guest is None:
                errors.append(Error(f"Room {room.number} sp_ticket_id {room.sp_ticket_id} missing guest",
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

