#!/usr/bin/env bash

set -e

ENV_FILE="/tmp/secrets.env"

problems() {
    2>&1 echo "Error: $*"
    exit 1
}

cleanup() {
    rm "$ENV_FILE"
}

[ -e "$ENV_FILE" ] || problems "unable to find env file"

trap cleanup EXIT

[ "$#" -ge 1 ] || problems "invalid args"
ACTION="$1"
shift
eval `cat "$ENV_FILE"`
export PGPASSWORD="$ROOMBAHT_DB_PASSWORD"

if [ "$ACTION" == "init" ] ; then
    ROOM_FILE="$2"
    STAFF_FILE="$3"
    shift 2
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/createStaffAndRooms.py" \
	"${ROOM_FILE}" \
	"${STAFF_FILE}"
elif [ "$ACTION" == "wipe" ] ; then
    psql -h "$ROOMBAHT_DB_HOST" -U postgres -tAc 'DROP DATABASE roombaht;'
    psql -h "$ROOMBAHT_DB_HOST" -U postgres -tAc "CREATE DATABASE roombaht;"
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" migrate
elif [ "$ACTION" == "manage" ] ; then
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" $*
else
    echo "invalid args"

fi
