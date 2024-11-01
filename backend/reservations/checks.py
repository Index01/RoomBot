from django.core.checks import Error, Warning, Info, register
from reservations.models import Room, Guest

def ticket_chain(p_guest, p_chain=[]):
    a_chain = [p_guest] + p_chain

    if not p_guest.transfer or p_guest.transfer == '':
        return a_chain

    try:
        a_guest = Guest.objects.get(ticket=p_guest.transfer)
    except Guest.DoesNotExist:
        return a_chain

    return ticket_chain(a_guest, a_chain)

@register(deploy=True)
def guest_drama_check(app_configs, **kwargs):
    errors = []
    guests = Guest.objects.all()


    for guest in guests:
        if guest.jwt == '' and guest.can_login:
            errors.append(Warning(f"Guest {guest.email} has an empty jwt field!",
                                  hint="Reset password via ux or user_edit"),
                          obj=guest)

        if guest.ticket and Guest.objects.filter(ticket = guest.ticket).count() > 1:
            errors.append(Error(f"Guest {guest.email}, ticket {guest.ticket} shared with other users"))

        guest_transfer_chain = ticket_chain(guest)
        chain_tail = [x for x in guest_transfer_chain if x.transfer == '']
        if len(chain_tail) == 0:
            errors.append(Error(f"Transfer chail tail not found {[x.ticket for x in guest_transfer_chain]}",
                          hint="Unable to find guest record w/o transfer in this chain." \
                                "Manually reconcile against SP exports.", obj=guest))

        for chain_guest in guest_transfer_chain:
            if chain_guest.transfer == '' \
               and chain_guest.ticket != '' \
                and chain_guest.room_set.count() > 0:
                try:
                    chain_room = Room.objects.get(guest=chain_guest)
                    if chain_room.is_placed and chain_guest.ticket != chain_room.sp_ticket_id:
                        errors.append(Warning(f"Placed room {chain_room.name_take3} {chain_room.number} ticket {chain_room.sp_ticket_id}" \
                                              f"does not match guest {guest.name}, ticket {guest.ticket}",
                                      hint="Manual reconciliation? Good luck, starfighter.",
                                      obj=guest))
                except Room.DoesNotExist:
                    errors.append(Warning(f"Unable to find corresponding room for {guest.email}, ticket {guest.ticket}",
                                          hint="Reimporting SP or manual reconciliation (or bug!)",
                                          obj=guest))

    for guest_email in Guest.objects.values('email').distinct():
        for guest in Guest.objects.filter(email=guest_email):
            guest_jwt = set([x.jwt for x in guest])
            if len(guest_jwt) > 1:
                errors.append(Error(f"Guest {guest.email} has {len(guest_jwt)} distinct jwt entries!",
                                    hint='Indicative of guest import bug. Will require manual reconciliation.',
                                    obj=guest))

    multi_room = [','.join([str(x) for x in Guest.objects.all() if x.room_set.count() > 1])]
    if len([x for x in multi_room if len(x) > 0]) > 0:
        errors.append(Error(f"Guest records with multiple associated rooms {multi_room}"))

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
                errors.append(Error(f"Original owner of {room.name_hotel} {room.number} with ticket {room.sp_ticket_id} not found",
                                    hint='Good luck, I guess?', obj=room))

            if room.guest is None:
                errors.append(Error(f"Room {room.number} ({room.name_hotel}) sp_ticket_id {room.sp_ticket_id} missing guest",
                                    hint='Manually reconcile w/ sources of truth', obj=room))

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

