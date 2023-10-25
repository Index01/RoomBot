import logging
import sys

from reservations.views.rooms import phrasing
from reservations.constants import ROOM_LIST
import reservations.config as roombaht_config
from .models import Room, Guest

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger("ViewLogger_ledger")


class RoomCounts:
    counts = {}

    def __init__(self):
        for room_type in ROOM_LIST.keys():
            self.counts[room_type] = {
                "available": Room.objects.filter(
                    name_take3=room_type, is_available=True
                ).count(),
                "allocated": 0,
                "shortage": 0,
                "orphan": 0,
                "transfer": 0,
            }

    def shortage(self, product):
        self.counts[product]["shortage"] += 1

    def allocated(self, product):
        self.counts[product]["allocated"] += 1

    def orphan(self, product):
        self.counts[product]["orphan"] += 1

    def transfer(self, product):
        self.counts[product]["transfer"] += 1

    def output(self):
        lines = []
        for room_type, counts in self.counts.items():
            if counts["orphan"] > 0:
                logger.info("Reunited %s %s orphans", counts["orphan"], room_type)

            if counts["shortage"] > 0:
                logger.warning(
                    "%s room short inventory by %s! available:%s, allocated:%s, transfer: %s, orphan: %s",
                    room_type,
                    counts["shortage"],
                    counts["available"],
                    counts["allocated"],
                    counts["transfer"],
                    counts["orphan"],
                )
            remaining = Room.objects.filter(
                name_take3=room_type, is_available=True
            ).count()

            line = f"{room_type} shortage: {counts['shortage']}, allocated: {counts['allocated']}, transfer: {counts['transfer']}, remaining: {remaining}, orphan: {counts['orphan']} (of {counts['available']} available)"
            logger.info(line)
            lines.append(line)

        return lines


class GuestLedger:
    def __init__(self, guest_rows):
        self.room_counts = RoomCounts()
        self.transferred_tickets = []
        # TODO(tb): sort the guest_rows alphabetically by the ticket field. Put all the transfer tickets at the end.
        self.guest_rows = guest_rows

    def lines(self):
        return self.room_counts.output()

    def short_product_code(self, product):
        for a_room, a_product in ROOM_LIST.items():
            if product in a_product:
                return a_room

        if product in ROOM_LIST.keys():
            return product

        raise Exception("Should never not find a short product code tho")

    def onboarding_email(self, guest_new, otp):
        if not roombaht_config.SEND_ONBOARDING:
            return

        hostname = my_url()
        time.sleep(5)
        body_text = f"""
            BleepBloopBleep, this is the Room Service RoomBaht for Room Swaps letting you know the floors have been cleaned and you have been assigned a room. No bucket or mop needed.
    
            After you login below you can view your current room, look at other rooms and send trade requests. This functionality is only available until Monday 11/7 at 5pm PST, so please make sure you are good with what you have or trade early.
    
            Goes without saying, but don't forward this email.
    
            This is your password, there are many like it but this one is yours. Once you use this password on a device, RoomBaht will remember you, but only on that device.
            Copy and paste this password. Because let’s face it, no one should trust humans to make passwords:
            {otp}
            {hostname}/login
    
            Good Luck, Starfighter.
    
        """
        send_email(
            [guest_new["email"]], "RoomService RoomBaht - Account Activation", body_text
        )

    def find_room(self, guest, assign_rooms=True, hotel="Ballys"):
        room_type = self.short_product_code(guest["product"])

        if not room_type:
            raise Exception(
                "Unable to actually find room type for %s" % guest["product"]
            )

        # We only auto-assign rooms if these criteria are met
        #  * must be available
        #  * must not be art - we should rarely see these as art rooms are almost always placed
        available_room = (
            Room.objects.filter(
                is_available=True,
                is_art=False,
                name_take3=room_type,
            )
            .order_by("?")
            .first()
        )
        if assign_rooms == False and available_room != None:
            available_room.number = 666
        if not available_room:
            logger.debug(
                "No room of type %s available. Product: %s", room_type, guest["product"]
            )
            logger.warning("No empty rooms available for %s", guest["email"])
            self.room_counts.shortage(self.short_product_code(guest["product"]))
            return None
        else:
            logger.debug(
                "Found free room of type %s: %s", room_type, available_room.number
            )

        return available_room

    def transfer_chain(self, ticket, depth=1):
        chain = []
        for row in self.guest_rows:
            if ticket == row["ticket_code"]:
                chain.append(row)
                if row["transferred_from_code"] != "":
                    print(depth)
                    a_chain = self.transfer_chain(ticket=row["transferred_from_code"], depth=depth+1)
                    if len(a_chain) == 0:
                        logger.debug(
                            "Unable to find recursive ticket for %s (depth %s)",
                            ticket,
                            depth,
                        )
                        return chain
                    chain += a_chain
                logger.debug(
                    "Found transfer ticket %s source (depth %s)", ticket, depth
                )

        return chain

    def reconcile_orphan_rooms(self):
        # rooms may be orphaned due to placement changes, data corruption, machine elves
        orphan_tickets = []

        def get_guest_obj(field, value):
            for guest in self.guest_rows:
                if (
                    field == "name"
                    and value == f"{guest['first_name']} {guest['last_name']}"
                ):
                    return guest

                if field == "ticket" and value == guest["ticket_code"]:
                    return guest

            return None

        orphan_rooms = Room.objects.filter(guest=None, is_available=False).exclude(
            primary=""
        )
        logger.debug("Attempting to reconcile %s orphan rooms", orphan_rooms.count())
        for room in orphan_rooms:
            guest = None
            # some validation
            if room.sp_ticket_id and room.is_comp:
                logger.warning(
                    "Room %s is comp'd and has ticket %s; skipping",
                    room.number,
                    room.sp_ticket_id,
                )
            # first check for a guest entry by sp_ticket_id
            try:
                if room.sp_ticket_id:
                    guest = Guest.objects.get(ticket=room.sp_ticket_id)
                    logger.info(
                        "Found guest %s by sp_ticket_id in DB for orphan %s room %s",
                        guest.email,
                        room.name_take3,
                        room.number,
                    )
            except Guest.DoesNotExist:
                pass

            if not guest:
                # then check for a guest entry by room number
                try:
                    guest = Guest.objects.get(room_number=room.number)
                    logger.info(
                        "Found guest %s by room_number in DB for orphan %s room %s",
                        guest.email,
                        room.name_take3,
                        room.number,
                    )
                except Guest.DoesNotExist:
                    pass

            if guest:
                # we found one, how lovely. associate room with it.
                room.guest = guest
                if room.primary != guest.name:
                    logger.warning(
                        "names do not match for orphan room %s (%s, %s, %s fuzziness)",
                        room.number,
                        room.primary,
                        guest.name,
                        fuzz.ratio(room.primary, guest.name),
                    )
                    continue

                if room.primary == "":
                    room.primary = guest.name

                self.room_counts.orphan(room.name_take3)
                room.save()
            else:
                # then check the guest list
                guest_obj = None
                if room.sp_ticket_id is not None:
                    guest_obj = get_guest_obj("ticket", room.sp_ticket_id)
                    if guest_obj:
                        logger.info(
                            "Found guest %s by ticket %s in CSV for orphan %s room %s",
                            guest_obj["email"],
                            room.sp_ticket_id,
                            room.name_take3,
                            room.number,
                        )
                        # if this is a transfer, need to account for those as well
                        if guest_obj["transferred_from_code"] != "":
                            chain = self.transfer_chain(guest_obj["transferred_from_code"])
                            if len(chain) > 0:
                                for chain_guest in chain:
                                    # add stubs to represent the transfers
                                    stub = Guest(
                                        name=f"{chain_guest['first_name']} {chain_guest['last_name']}".title(),
                                        email=chain_guest["email"],
                                        ticket=chain_guest["ticket_code"],
                                    )
                                    stub.save()
                                    orphan_tickets.append(chain_guest["ticket_code"])

                if guest_obj:
                    # we have one, that's nice
                    otp = phrasing()
                    self.guest_update(guest_obj, otp, room)
                    self.onboarding_email(guest_obj, otp)
                else:
                    if room.is_comp:
                        logger.debug(
                            "Ignoring comp'd %s room %s, guest %s",
                            room.name_take3,
                            room.number,
                            room.primary,
                        )
                    else:
                        logger.warning(
                            "Unable to find guest %s for (non-comp) orphan room %s",
                            room.primary,
                            room.number,
                        )

                        possibilities = [
                            x
                            for x in process.extract(
                                room.primary,
                                [
                                    f"{x['first_name']} {x['last_name']}"
                                    for x in self.guest_rows
                                ],
                            )
                            if x[1] > 85
                        ]
                        if len(possibilities) > 0:
                            logger.warning(
                                "Found %s fuzzy name possibilities in CSV for %s in orphan room %s: %s",
                                len(possibilities),
                                room.primary,
                                room.number,
                                ",".join([f"{x[0]}:{x[1]}" for x in possibilities]),
                            )
                    continue

            if room.sp_ticket_id:
                orphan_tickets.append(room.sp_ticket_id)

        return orphan_tickets

    def guest_update(self, guest_dict, otp, room, og_guest=None):
        ticket_code = guest_dict["ticket_code"]
        email = guest_dict["email"]
        guest = None
        guest_changed = False
        try:
            # placed rooms may already have records
            # also sometimes people transfer rooms to themselves
            #   because why the frak not
            guest = Guest.objects.get(ticket=ticket_code, email=email)
            logger.debug("Found existing ticket %s for %s", ticket_code, email)
            if guest.room_number:
                if guest.room_number == room.number:
                    logger.debug(
                        "Existing guest %s already associated with room %s (%s)",
                        email,
                        room.number,
                        room.name_tak3,
                    )
                else:
                    # transfers for placed users
                    logger.warning(
                        "Existing guest %s not moving from %s to %s (%s)",
                        email,
                        guest.room_number,
                        room.number,
                        room.name_take3,
                    )

                return

            logger.debug(
                "Existing guest %s assigned to %s (%s)",
                email,
                room.number,
                room.name_take3,
            )
            guest.room_number = room.number
            guest_changed = True

        except Guest.DoesNotExist:
            # but most of the time the guest does not exist yet
            guest = Guest(
                name=f"{guest_dict['first_name']} {guest_dict['last_name']}".title(),
                ticket=guest_dict["ticket_code"],
                jwt=otp,
                email=email,
                room_number=room.number,
            )
            logger.debug(
                "New guest %s in room %s (%s)", email, room.number, room.name_take3
            )
            guest_changed = True

        # save guest (if needed) and then...
        if guest_changed:
            guest.save()

        if room.primary != "" and room.primary != guest.name:
            logger.warning(
                "Room %s already has a name set: %s, guest %s!",
                room.number,
                room.primary,
                guest.name,
            )

        # unassociated original owner (if present)
        if room.guest and og_guest:
            if room.guest != og_guest:
                logger.warning(
                    "Unexpected original owner %s for room %s",
                    room.guest.email,
                    room.number,
                )

            room.guest.room_number = None
            logger.debug(
                "Removing original owner %s for room %s", room.guest.email, room.number
            )
            room.guest.save()

        # update room
        room.guest = guest
        room.is_available = False

        room.primary = guest.name
        room.save()

    def deal_with_transfers(self, guest, trans_code, guest_entries):
        # Transfered ticket...
        existing_guest = None
        ticket_code = guest["ticket_code"]
        try:
            existing_guest = Guest.objects.get(ticket=trans_code)
            logger.info(f"esisting guest found: {existing_guest.room_number}")
        except Guest.DoesNotExist:
            # sometimes this happens due to transfers showing up earlier in the sp export than
            # the origial ticket. so we go through the full set of rows
            chain = self.transfer_chain(trans_code)
            if len(chain) == 0:
                logger.warning(
                    "Ticket transfer (%s) but no previous guest found", trans_code
                )
                return

            for chain_guest in chain:
                # add stub guests
                stub = Guest(
                    name=f"{chain_guest['first_name']} {chain_guest['last_name']}".title(),
                    email=chain_guest["email"],
                    ticket=chain_guest["ticket_code"],
                )
                stub.save()

                self.transferred_tickets.append(chain_guest["ticket_code"])

            room = self.find_room(guest)

            email_chain = ",".join([x["email"] for x in chain])
            if guest_entries.count() == 0:
                logger.debug(
                    "Processing transfer %s (%s) from %s to (new guest) %s",
                    trans_code,
                    ticket_code,
                    email_chain,
                    guest["email"],
                )
                otp = phrasing()
                self.guest_update(guest, otp, room)
            else:
                logger.debug(
                    "Processing transfer %s (%s) from %s to %s",
                    trans_code,
                    ticket_code,
                    email_chain,
                    guest["email"],
                )
                otp = guest_entries[0].jwt
                self.guest_update(guest, otp, room)

            if room.number != 666:
                self.room_counts.transfer(room.name_take3)

            return

        if existing_guest.room_number != None:
            existing_room = Room.objects.get(number=existing_guest.room_number)
        else:
            return

        if guest_entries.count() == 0:
            # Transferring to new guest...
            logger.debug(
                "Processing placed transfer %s (%s) from %s to (new guest) %s",
                trans_code,
                ticket_code,
                existing_guest.email,
                guest["email"],
            )
            otp = phrasing()
            self.guest_update(guest, otp, existing_room, og_guest=existing_guest)
            self.onboarding_email(guest, otp)
        else:
            # Transferring to existing guest...
            logger.debug(
                "Processing placed transfer %s (%s) from %s to %s",
                trans_code,
                ticket_code,
                existing_guest.email,
                guest["email"],
            )
            # i think this will result in every jwt field being the same? guest entries
            # are kept around as part of transfers (ticket/email uniq) and when someone
            # has multiple rooms (email/room uniq)
            otp = guest_entries[0].jwt
            self.guest_update(guest, otp, existing_room, og_guest=existing_guest)

        self.room_counts.transfer(existing_room.name_take3)

    def walk(self, orphan_tickets=[]):
        for guest_obj in self.guest_rows:
            guest_entries = Guest.objects.filter(email=guest_obj["email"])
            trans_code = guest_obj["transferred_from_code"]
            ticket_code = guest_obj["ticket_code"]

            if ticket_code in self.transferred_tickets:
                logger.debug("Skipping transferred ticket %s", ticket_code)
                continue

            if ticket_code in orphan_tickets:
                logger.debug("Skipping ticket %s from orphan processing", ticket_code)
                continue

            if ticket_code in roombaht_config.IGNORE_TRANSACTIONS:
                logger.info(
                    "Skipping ticket %s as it is on our ignore list", ticket_code
                )
                continue

            if trans_code == "" and guest_entries.count() == 0:
                # Unknown ticket, no transfer; new user
                room = self.find_room(guest_obj)
                if not room:
                    # sometimes this happens due to room transfers not being complete.
                    logger.warning(
                        "No empty rooms available for %s", guest_obj["email"]
                    )
                    self.room_counts.shortage(
                        self.short_product_code(guest_obj["product"])
                    )
                    continue

                logger.info(
                    "Email doesnt exist: %s. Creating new guest contact.",
                    guest_obj["email"],
                )
                otp = phrasing()
                self.guest_update(guest_obj, otp, room)
                self.onboarding_email(guest_obj, otp)
                self.room_counts.allocated(room.name_take3)
            elif trans_code == "" and guest_entries.count() > 0:
                # There are a few cases that could pop up here
                # * admins / staff
                # * people share email addresses and soft-transfer rooms in sp
                if (
                    len([x.ticket for x in guest_entries if x.ticket == ticket_code])
                    == 0
                ):
                    room = self.find_room(guest_obj)
                    if not room:
                        logger.warning(
                            "No empty rooms available for %s", guest_entries[0].email
                        )
                        self.room_counts.shortage(
                            self.short_product_code(guest_obj["product"])
                        )
                        continue

                    logger.debug(
                        "assigning room %s to (unassigned ticket/room) %s",
                        room.number,
                        guest_entries[0].email,
                    )
                    self.guest_update(guest_obj, guest_entries[0].jwt, room)
                    self.room_counts.allocated(room.name_take3)
                else:
                    logger.warning(
                        "Not sure how to handle non-transfer, existing user ticket %s",
                        ticket_code,
                    )

            elif trans_code != "":
                self.deal_with_transfers(guest_obj, trans_code, guest_entries)

            else:
                logger.warning("Not sure how to handle ticket %s", ticket_code)

    def create_only(self):
        guestz = Guest.objects.all()
        for row in self.guest_rows:
            if len(guestz.filter(ticket=row["ticket_code"])) == 0:
                otp = phrasing()
                guest = Guest(
                    name=f"{row['first_name']} {row['last_name']}".title(),
                    ticket=row["ticket_code"],
                    jwt=otp,
                    email=row['email'],
                )
                guest.save()
