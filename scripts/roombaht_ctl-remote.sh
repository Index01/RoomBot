#!/usr/bin/env bash

set -e

if [ -z "$ENV_FILE" ] ; then
    ENV_FILE="/tmp/secrets.env"
fi

problems() {
    2>&1 echo "Error: $*"
    exit 1
}

cleanup() {
    rm "$ENV_FILE"
    if [ -n "$ROOM_FILE" ] ; then
	rm "$ROOM_FILE"
    fi
    if [ -n "$STAFF_FILE" ] ; then
	rm "$STAFF_FILE"
    fi
}

[ -e "$ENV_FILE" ] || problems "unable to find env file"

trap cleanup EXIT

[ "$#" -ge 1 ] || problems "invalid args"
ACTION="$1"
shift
source "$ENV_FILE"
export PGPASSWORD="$ROOMBAHT_DB_PASSWORD"

if [ "$ACTION" == "init" ] ; then
    ROOM_FILE="$1"
    STAFF_FILE="$2"
    shift 2
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/createStaffAndRooms.py" \
	"${ROOM_FILE}" \
	"${STAFF_FILE}"
elif [ "$ACTION" == "clone_db" ] ; then
    if [ "$ROOMBAHT_DB" == "roombaht" ] ; then
	problems "can't clone prod to prod"
    fi
    dropdb -h "$ROOMBAHT_DB_HOST" -U postgres "$ROOMBAHT_DB"
    createdb -h "$ROOMBAHT_DB_HOST" -U postgres -T roombaht "$ROOMBAHT_DB"
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" migrate
elif [ "$ACTION" == "wipe" ] ; then
    dropdb -h "$ROOMBAHT_DB_HOST" -U postgres "$ROOMBAHT_DB"
    createdb -h "$ROOMBAHT_DB_HOST" -U postgres "$ROOMBAHT_DB"
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" migrate
elif [ "$ACTION" == "manage" ] ; then
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" $*
else
    echo "invalid args"

fi
