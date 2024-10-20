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

init() {
    nohup "${SCRIPTDIR}/start_backend_dev.sh" &> "$LOG" &
    BACKEND_PID="$!"
    sleep 5
}

run() {
    "${SCRIPTDIR}/manage_dev" loaddata test_users
    "$TAVERN" backend/tavern/test_login.tavern.yml

    "${SCRIPTDIR}/manage_dev" loaddata test_users
    "${SCRIPTDIR}/manage_dev" loaddata test_rooms
    "$TAVERN" backend/tavern/test_room_swap.tavern.yml
    "$TAVERN" backend/tavern/test_admin.tavern.yml

    SUCCESS="yea girl"
}

SQLITE="${ROOTDIR}/test.sqlite"
TAVERN="${ROOTDIR}/backend/venv/bin/tavern-ci"
LOG="${ROOTDIR}/test.log"

if [ -e "$SQLITE" ] ; then
    rm -rf "$SQLITE"
fi

export ROOMBAHT_CONFIG="${ROOTDIR}/test.env"
trap cleanup EXIT

if [ "$1" == "init" ] ; then
    init
    exit 0
elif [ "$1" == "run" ] ; then
    run
    exit 0
elif [ "$!" == "cleanup" ] ; then
    cleanup
    exit 0
else
    init
    run
    cleanup
    exit 0
fi
