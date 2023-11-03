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
	"/opt/roombaht-backend/manage.py" "create_rooms" "${ROOM_FILE}" --hotel ballys
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" "create_staff" "${STAFF_FILE}"
elif [ "$ACTION" == "clone_db" ] ; then
    if [ "$ROOMBAHT_DB" == "roombaht" ] ; then
	problems "can't clone prod to prod"
    fi
    SOURCE_DB="roombaht"
    while getopts "d:" arg; do
	case $arg in
	    d)
		SOURCE_DB="$OPTARG"
		;;
	    *)
		problems "Unknown option passed to clone"
		;;
	esac
    done
    if psql -h "$ROOMBAHT_DB_HOST" -U postgres -l | grep -q "$ROOMBAHT_DB" ; then
	dropdb -h "$ROOMBAHT_DB_HOST" -U postgres "$ROOMBAHT_DB"
    fi
    createdb -h "$ROOMBAHT_DB_HOST" -U postgres -T "$SOURCE_DB" "$ROOMBAHT_DB"
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
