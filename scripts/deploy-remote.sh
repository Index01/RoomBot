#!/usr/bin/env bash

set -e

BACKEND_ARTIFACT="/tmp/roombaht-backend.tgz"
FRONTEND_ARTIFACT="/tmp/roombaht-frontend.tgz"

BACKEND_DIR="/opt/roombaht-backend"
FRONTEND_DIR="/opt/roombaht-frontend"

ENV_FILE="/tmp/secrets.env"

problems() {
    2>&1 echo "Error: $*"
    exit 1
}

cleanup() {
    rm "$ENV_FILE" "$BACKEND_ARTIFACT" "$FRONTEND_ARTIFACT"
}

[ -e "$BACKEND_ARTIFACT" ] || problems "unable to find backend artifact"
[ -e "$FRONTEND_ARTIFACT" ] || problems "unable to find frontend artifact"
[ -e "$ENV_FILE" ] || problems "unable to find env file"

trap cleanup EXIT

# shellcheck disable=SC1090
source "$ENV_FILE"
export PGPASSWORD="$ROOMBAHT_DB_PASSWORD"

if [ -d "${BACKEND_DIR}.old" ] ; then
    rm -rf "${BACKEND_DIR}.old"
fi

mv "$BACKEND_DIR" "${BACKEND_DIR}.old"
tar -C "/opt" -xzvf "$BACKEND_ARTIFACT"
if [ -d "${BACKEND_DIR}/.old/venv" ] ; then
    cp -r "${BACKEND_DIR}.old/venv" "${BACKEND_DIR}/venv"
fi

chown -R roombaht: "$BACKEND_DIR"
chmod -R o-rwx "$BACKEND_DIR"

sudo -u roombaht -- bash -c "test -d ${BACKEND_DIR}/venv || ( mkdir ${BACKEND_DIR}/venv && virtualenv -p python3 ${BACKEND_DIR}/venv ) && ${BACKEND_DIR}/venv/bin/python3 -m pip install --upgrade pip"
sudo -u roombaht -- bash -c "${BACKEND_DIR}/venv/bin/pip install -r ${BACKEND_DIR}/requirements.txt --upgrade"

if ! psql -h "$ROOMBAHT_DB_HOST" -U postgres -l | grep -q roombaht ; then
    psql -h "$ROOMBAHT_DB_HOST" -U postgres -tAc "CREATE DATABASE roombaht;"
fi
sed -e "s/@SECRET_KEY@/${ROOMBAHT_DJANGO_SECRET_KEY}/" \
    -e "s/@EMAIL_HOST_USER@/${ROOMBAHT_EMAIL_HOST_USER}/" \
    -e "s/@EMAIL_HOST_PASSWORD@/${ROOMBAHT_EMAIL_HOST_PASSWORD}/" \
    -e "s/@DB_PASSWORD@/${ROOMBAHT_DB_PASSWORD}/" \
    -e "s/@DB_HOST@/${ROOMBAHT_DB_HOST}/" \
    -e "s/@SEND_MAIL@/${ROOMBAHT_SEND_MAIL}/" \
    -e "s%@TEMP@%${ROOMBAHT_TMP}%" \
    -e "s/@JWT_KEY@/${ROOMBAHT_JWT_KEY}/" \
    -e "s/@HOST@/${ROOMBAHT_HOST}/" \
    "${BACKEND_DIR}/config/roombaht-systemd.conf" \
    > "/etc/systemd/system/roombaht.service"
chmod o-rwx "/etc/systemd/system/roombaht.service"
systemctl daemon-reload
systemctl stop roombaht
"${BACKEND_DIR}/venv/bin/python" \
    "${BACKEND_DIR}/manage.py" migrate
systemctl start roombaht

if [ -d "${FRONTEND_DIR}.old" ] ; then
    rm -rf "${FRONTEND_DIR}.old"
fi

mv "$FRONTEND_DIR" "${FRONTEND_DIR}.old"
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
