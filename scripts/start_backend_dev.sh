#!/usr/bin/env bash

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

source backend/venv/bin/activate
which python

cd backend && \
python manage.py migrate && \
exec python manage.py runserver 0.0.0.0:8000
