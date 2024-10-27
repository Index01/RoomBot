#!/usr/bin/env bash

set -e

if [ -n "$ROOMBAHT_CONFIG" ] ; then
    echo "Using alternative config ${ROOMBAHT_CONFIG}"
    if [ ! -e "$ROOMBAHT_CONFIG" ] ; then
	echo "Unable to open alternate config, lollll"
	exit 2
    fi
else
    ROOMBAHT_CONFIG="dev.env"
fi
source "$ROOMBAHT_CONFIG"
printenv | grep ROOMBAHT

./scripts/manage_dev migrate
./scripts/manage_dev runserver 0.0.0.0:8000
