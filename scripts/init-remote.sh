#!/usr/bin/env bash

set -e

ENV_FILE="/tmp/secrets.env"
problems() {
    2>&1 echo "Error: $*"
    exit 1
}

cleanup() {
    rm -f "$ENV_FILE"
    if [ -n "$ROOM_FILE" ] ; then
	rm -f "${ROOM_FILE}"
    fi
    if [ -n "$STAFF_FILE" ] ; then
	rm -f "${STAFF_FILE}"
    fi
}

trap cleanup EXIT

[ $# == 2 ] || problems "invalid args"

ROOM_FILE="$1"
STAFF_FILE="$2"

eval `cat "$ENV_FILE"`

"/opt/roombaht-backend/venv/bin/python3" \
    "/opt/roombaht-backend/createStaffAndRooms.py" \
    "${ROOM_FILE}" \
    "${STAFF_FILE}"
