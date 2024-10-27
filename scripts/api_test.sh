#!/usr/bin/env bash

set -e
SCRIPTDIR=$( cd "${0%/*}" && pwd)
ROOTDIR="${SCRIPTDIR%/*}"

usage() {
    echo "${0}                               init, test, cleanup"
    echo "${0}      test                     execute tests"
    echo "${0}      init                     initialize test environment"
    echo "${0}      cleanup                  cleanup test environment"
}

cleanup() {
    if [ -e "$SQLITE" ] ; then
	rm "$SQLITE"
    fi
    PIDS="$(pgrep -f '.*manage.py runserver.*')"
    if [ -n "$PIDS" ] ; then
	for pid in $PIDS ; do
	    if ps "$pid" &> /dev/null ; then
		kill "$pid"
	    fi
	done
    fi
}

init() {
    nohup "${SCRIPTDIR}/start_backend_dev.sh" < /dev/null &> "$LOG" & disown
    sleep 5
}

run_logs() {
    if [ -z "$SUCCESS" ] && [ -e "$LOG" ] ; then
	cat "$LOG"
    fi
}

run() {
    trap run_logs EXIT
    # fixture based basic login / auth flow
    "${SCRIPTDIR}/manage_dev" loaddata test_users
    "$TAVERN" backend/tavern/test_login.tavern.yml

    # fixture based room swaps and (basic) admin functionality
    "${SCRIPTDIR}/manage_dev" loaddata test_users
    "${SCRIPTDIR}/manage_dev" loaddata test_rooms
    "$TAVERN" backend/tavern/test_room_swap.tavern.yml
    "$TAVERN" backend/tavern/test_admin.tavern.yml

    # sample data based data loading
    rm "$SQLITE"
    {
	"${SCRIPTDIR}/manage_dev" migrate ;
	"${SCRIPTDIR}/manage_dev" create_rooms --hotel-name Ballys "${ROOTDIR}/samples/exampleBallysRoomList.csv" --preserve --force ;
	"${SCRIPTDIR}/manage_dev" create_rooms --hotel-name Nugget "${ROOTDIR}/samples/exampleNuggetRoomList.csv" --preserve --force
    } >> "$LOG"

    SUCCESS="yea girl"
}

SQLITE="${ROOTDIR}/backend/test.sqlite"
TAVERN="${ROOTDIR}/backend/venv/bin/tavern-ci"
LOG="${ROOTDIR}/test.log"

if [ -e "$SQLITE" ] ; then
    rm -rf "$SQLITE"
fi

export ROOMBAHT_CONFIG="${ROOTDIR}/test.env"

if [ "$1" == "init" ] ; then
    init
    exit 0
elif [ "$1" == "run" ] ; then
    run
    exit 0
elif [ "$1" == "cleanup" ] ; then
    cleanup
    exit 0
elif [ "$#" == 0 ] ; then
    trap cleanup EXIT
    init
    run
    cleanup
    exit 0
else
    usage
    exit 1
fi
