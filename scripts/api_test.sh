#!/usr/bin/env bash

set -e
SCRIPTDIR=$( cd "${0%/*}" && pwd)
ROOTDIR="${SCRIPTDIR%/*}"

cleanup() {
    if [ -e "$SQLITE" ] ; then
        rm "$SQLITE"
    fi
    "${SCRIPTDIR}/test_infra.sh" stop
    if [ -z "$SUCCESS" ] && [ -e "$LOG" ] ; then
        cat "$LOG"
    fi
    "${SCRIPTDIR}/test_infra.sh" report
}

init() {
    "${SCRIPTDIR}/test_infra.sh" start
    local COUNT=5
    while [ "$COUNT" -gt 0 ] ; do
        if ! curl -o /dev/null -s http://localhost:8000/api/login/ ; then
            sleep 1
            COUNT="$((COUNT - 1))"
	    if [ "$COUNT" -le 0 ] ; then
		echo "Unable to start backend???"
		exit 1
	    fi
        else
            COUNT=0
        fi
    done
}

manage() {
    "${ROOTDIR}/backend/venv/bin/coverage" \
	run -a "${ROOTDIR}/backend/manage.py" $*
}

run() {
    # first run tests with static fixtures
    "${SCRIPTDIR}/manage_dev" loaddata test_users
    "$TAVERN" backend/tavern/test_login.tavern.yml

    "${SCRIPTDIR}/manage_dev" loaddata test_users
    "${SCRIPTDIR}/manage_dev" loaddata test_rooms
    "$TAVERN" backend/tavern/test_room_swap.tavern.yml
    "$TAVERN" backend/tavern/test_admin.tavern.yml
    "$TAVERN" backend/tavern/test_reports.tavern.yml

    # we want to test cli tools
    source "${ROOTDIR}/test.env"

    manage room_list &>> "$LOG"
    manage room_list -t Queen &>> "$LOG"
    manage room_show --hotel ballys 503 &>> "$LOG"
    manage user_show testadmin@example.com &>> "$LOG"
    manage user_show testuser1@example.com &>> "$LOG"
    manage check --deploy &>> "$LOG"

    # then run tests following typical import data flow
    "${SCRIPTDIR}/manage_dev" flush --noinput &>> "$LOG"
    "${SCRIPTDIR}/manage_dev" migrate &>> "$LOG"
    manage load_staff "${ROOTDIR}/samples/exampleMainStaffList.csv"
    manage load_rooms \
           "${ROOTDIR}/samples/exampleBallysRoomList.csv" \
           --hotel ballys --preserve --force \
           --default-check-in="1999/1/1" --default-check-out="1999/1/10"
    manage load_rooms \
           "${ROOTDIR}/samples/exampleNuggetRoomList.csv" \
           --hotel nugget --preserve --force \
           --default-check-in "1999/1/1" --default-check-out "1999/1/10"

    "${SCRIPTDIR}/manage_dev" loaddata test_users
    "$TAVERN" backend/tavern/test_guests.tavern.yml
    manage room_list &>> "$LOG"
    manage room_list -t Queen &>> "$LOG"
    manage room_show --hotel ballys 400 &>> "$LOG"
    manage room_show --hotel nugget 110 &>> "$LOG"
    manage check --deploy &>> "$LOG"

    # then run tests following typical import data flow
    source "${ROOTDIR}/test.env"
    "${SCRIPTDIR}/manage_dev" flush --noinput
    "${SCRIPTDIR}/manage_dev" migrate
    manage load_staff "${ROOTDIR}/samples/exampleMainStaffList.csv"
    manage load_rooms \
           "${ROOTDIR}/samples/exampleBallysRoomList.csv" \
           --hotel ballys --preserve --force \
           --default-check-in="1999/1/1" --default-check-out="1999/1/10"
    manage load_rooms \
           "${ROOTDIR}/samples/exampleNuggetRoomList.csv" \
           --hotel nugget --preserve --force \
           --default-check-in "1999/1/1" --default-check-out "1999/1/10"

    SUCCESS="yea girl"
}

SQLITE="${ROOTDIR}/backend/test.sqlite"
export PYTHONPATH="${ROOTDIR}/backend/tavern"
export ROOTDIR
TAVERN="${ROOTDIR}/backend/venv/bin/tavern-ci"
LOG="${ROOTDIR}/test.log"

if [ -e "$SQLITE" ] ; then
    rm -rf "$SQLITE"
fi

export ROOMBAHT_CONFIG="${ROOTDIR}/test.env"

trap cleanup EXIT
init
run
