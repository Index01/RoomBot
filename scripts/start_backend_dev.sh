#!/usr/bin/env bash

source secrets.env
export ROOMBAHT_DJANGO_SECRET_KEY
export ROOMBAHT_DB_PASSWORD
export ROOMBAHT_DB_HOST
export ROOMBAHT_EMAIL_HOST_USER
export ROOMBAHT_EMAIL_HOST_PASSWORD
export ROOMBAHT_SEND_MAIL
export DJANGO_SETTINGS_MODULE
export PGPASSWORD="$ROOMBAHT_DB_PASSWORD"
echo $ROOMBAHT_DJANGO_SECRET_KEY

source backend/venv/bin/activate
which python

cd backend && \
python manage.py migrate && \
python manage.py runserver 0.0.0.0:8080