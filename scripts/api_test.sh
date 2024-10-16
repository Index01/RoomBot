#!/usr/bin/env bash

set -e
SCRIPTDIR=$( cd "${0%/*}" && pwd)
ROOTDIR="${SCRIPTDIR%/*}"

cleanup() {
    if [ -n "$BACKEND_PID" ] ; then
	kill "$BACKEND_PID"
    fi
    if [ -e "$SQLITE" ] ; then
	rm "$SQLITE"
    fi
    if [ -z "$SUCCESS" ] && [ -e "$LOG" ] ; then
	cat "$LOG"
    fi
}

SQLITE="${ROOTDIR}/test.sqlite"
TAVERN="${ROOTDIR}/backend/venv/bin/tavern-ci"
LOG="${ROOTDIR}/test.log"

if [ -e "$SQLITE" ] ; then
    rm -rf "$SQLITE"
fi

export ROOMBAHT_CONFIG="${ROOTDIR}/test.env"

trap cleanup EXIT

"${SCRIPTDIR}/start_backend_dev.sh" &> "$LOG" &
BACKEND_PID="$!"
sleep 5

"${SCRIPTDIR}/manage_dev" loaddata test_users
"$TAVERN" backend/tavern/test_login.tavern.yml

"${SCRIPTDIR}/manage_dev" loaddata test_users
"${SCRIPTDIR}/manage_dev" loaddata test_rooms
"$TAVERN" backend/tavern/test_room_swap.tavern.yml
SUCCESS="yea girl"
