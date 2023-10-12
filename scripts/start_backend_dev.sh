#!/usr/bin/env bash

source dev.env
printenv | grep ROOMBAHT

source backend/venv/bin/activate
which python

cd backend && \
python manage.py migrate && \
python manage.py runserver 0.0.0.0:8080
