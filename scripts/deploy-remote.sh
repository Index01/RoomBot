#!/usr/bin/env bash

set -e

OLD_RELEASES=5
BACKEND_ARTIFACT="/tmp/roombaht-backend.tgz"
FRONTEND_ARTIFACT="/tmp/roombaht-frontend.tgz"

BACKEND_DIR="/opt/roombaht-backend"
FRONTEND_DIR="/opt/roombaht-frontend"

ENV_FILE="/tmp/secrets.env"

NOW="$(date '+%m%d%Y-%H%M')"

problems() {
    2>&1 echo "Error: $*"
    exit 1
}

cleanup() {
    rm "$ENV_FILE"
    rm "$BACKEND_ARTIFACT" "$FRONTEND_ARTIFACT"
}

[ -e "$BACKEND_ARTIFACT" ] || problems "unable to find backend artifact"
[ -e "$FRONTEND_ARTIFACT" ] || problems "unable to find frontend artifact"
[ -e "$ENV_FILE" ] || problems "unable to find env file"

trap cleanup EXIT

# shellcheck disable=SC1090
source "$ENV_FILE"
export PGPASSWORD="$ROOMBAHT_DB_PASSWORD"

# load the backend
if [ -d "${BACKEND_DIR}.old" ] ; then
    rm -rf "${BACKEND_DIR}.old"
fi

# keep some archives for rollback
if [ -d "$BACKEND_DIR" ] ; then
    mv "$BACKEND_DIR" "${BACKEND_DIR}-${NOW}"
    for old in `find /opt -name 'roombaht-backend-*' -type d | sort | head -n "-${OLD_RELEASES}"` ; do
	rm -rf "$old"
    done
fi

tar -C "/opt" -xzvf "$BACKEND_ARTIFACT"
if [ -d "${BACKEND_DIR}/.old/venv" ] ; then
    cp -r "${BACKEND_DIR}.old/venv" "${BACKEND_DIR}/venv"
fi

chown -R roombaht: "$BACKEND_DIR"
chmod -R o-rwx "$BACKEND_DIR"

sudo -u roombaht -- bash -c "test -d ${BACKEND_DIR}/venv || ( mkdir ${BACKEND_DIR}/venv && virtualenv -p python3 ${BACKEND_DIR}/venv ) && ${BACKEND_DIR}/venv/bin/python3 -m pip install --upgrade pip"
sudo -u roombaht -- bash -c "${BACKEND_DIR}/venv/bin/pip install -r ${BACKEND_DIR}/requirements.txt --upgrade"

if ! psql -h "$ROOMBAHT_DB_HOST" -U postgres -l | grep -q "$ROOMBAHT_DB" ; then
    psql -h "$ROOMBAHT_DB_HOST" -U postgres -tAc "CREATE DATABASE ${ROOMBAHT_DB};"
fi
sed -e "s/@SECRET_KEY@/${ROOMBAHT_DJANGO_SECRET_KEY}/" \
    -e "s/@EMAIL_HOST_USER@/${ROOMBAHT_EMAIL_HOST_USER}/" \
    -e "s/@EMAIL_HOST_PASSWORD@/${ROOMBAHT_EMAIL_HOST_PASSWORD}/" \
    -e "s/@DB_PASSWORD@/${ROOMBAHT_DB_PASSWORD}/" \
    -e "s/@DB_NAME@/${ROOMBAHT_DB}/" \
    -e "s/@DB_HOST@/${ROOMBAHT_DB_HOST}/" \
    -e "s/@SEND_MAIL@/${ROOMBAHT_SEND_MAIL}/" \
    -e "s%@TEMP@%${ROOMBAHT_TMP}%" \
    -e "s/@JWT_KEY@/${ROOMBAHT_JWT_KEY}/" \
    -e "s/@HOST@/${ROOMBAHT_HOST}/" \
    -e "s/@LOGLEVEL@/${ROOMBAHT_LOGLEVEL}"/ \
    -e "s/@SEND_ONBOARDING@/${ROOMBAHT_SEND_ONBOARDING}/" \
    -e "s/@IGNORE_TRANSACTIONS@/${ROOMBAHT_IGNORE_TRANSACTIONS}/" \
    -e "s/@DEV_MAIL@/${ROOMBAHT_DEV_MAIL}/" \
    -e "s/@GUEST_HOTELS@/${ROOMBAHT_GUEST_HOTELS}/" \
    "${BACKEND_DIR}/config/roombaht-systemd.conf" \
    > "/etc/systemd/system/roombaht.service"
chmod o-rwx "/etc/systemd/system/roombaht.service"
systemctl daemon-reload
systemctl stop roombaht
"${BACKEND_DIR}/venv/bin/python" \
    "${BACKEND_DIR}/manage.py" migrate
systemctl start roombaht

sed -e "s/@SECRET_KEY@/${ROOMBAHT_DJANGO_SECRET_KEY}/" \
    -e "s/@EMAIL_HOST_USER@/${ROOMBAHT_EMAIL_HOST_USER}/" \
    -e "s/@EMAIL_HOST_PASSWORD@/${ROOMBAHT_EMAIL_HOST_PASSWORD}/" \
    -e "s/@DB_PASSWORD@/${ROOMBAHT_DB_PASSWORD}/" \
    -e "s/@DB_NAME@/${ROOMBAHT_DB}/" \
    -e "s/@DB_HOST@/${ROOMBAHT_DB_HOST}/" \
    -e "s/@SEND_MAIL@/${ROOMBAHT_SEND_MAIL}/" \
    -e "s%@TEMP@%${ROOMBAHT_TMP}%" \
    -e "s/@JWT_KEY@/${ROOMBAHT_JWT_KEY}/" \
    -e "s/@HOST@/${ROOMBAHT_HOST}/" \
    -e "s/@LOGLEVEL@/${ROOMBAHT_LOGLEVEL}"/ \
    -e "s/@SEND_ONBOARDING@/${ROOMBAHT_SEND_ONBOARDING}/" \
    -e "s/@IGNORE_TRANSACTIONS@/${ROOMBAHT_IGNORE_TRANSACTIONS}/" \
    -e "s/@ONBOARDING_BATCH@/${ROOMBAHT_ONBOARDING_BATCH}/" \
    -e "s/@DEV_MAIL@/${ROOMBAHT_DEV_MAIL}/" \
    "${BACKEND_DIR}/scripts/roombaht-oob.sh" \
    > "/opt/roombaht-backend/scripts/roombaht-oob"
chmod 0770 "/opt/roombaht-backend/scripts/roombaht-oob"
chown roombaht: "/opt/roombaht-backend/scripts/roombaht-oob"
cp /opt/roombaht-backend/scripts/roombaht-oob.cron \
   /etc/cron.d/roombaht-oob

# load the frontend
if [ -d "$FRONTEND_DIR" ] ; then
    mv "$FRONTEND_DIR" "${FRONTEND_DIR}-${NOW}"
    for old in `find /opt -name 'roombahtt-frontend-*' -type d | sort | head -n "-${OLD_RELEASES}"` ; do
	rm -rf "$old"
    done
fi

tar -C /opt -xzvf "$FRONTEND_ARTIFACT"

chown -R roombaht: "$FRONTEND_DIR"

if [ -e "/etc/nginx/sites-enabled/roombaht" ] ; then
    rm "/etc/nginx/sites-enabled/roombaht"
fi

sed -e "s/@ROOMBAHT_HOST@/${ROOMBAHT_HOST}/" \
    "${BACKEND_DIR}/config/roombaht-nginx.conf" \
    > "/etc/nginx/sites-enabled/roombaht"

if [ -e "/etc/nginx/sites-enabled/default" ] ; then
    rm "/etc/nginx/sites-enabled/default"
fi

systemctl reload nginx
