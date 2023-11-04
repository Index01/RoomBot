#!/usr/bin/env bash

set -e

if [ -z "$ENV_FILE" ] ; then
    ENV_FILE="/tmp/secrets.env"
fi

problems() {
    2>&1 echo "Error: $*"
    exit 1
}

cleanup() {
    rm "$ENV_FILE"
    if [ -n "$ROOM_FILE" ] ; then
	rm "$ROOM_FILE"
    fi
    if [ -n "$STAFF_FILE" ] ; then
	rm "$STAFF_FILE"
    fi
    if [ -n "$BACKEND_ARTIFACT" ] ; then
	rm "$BACKEND_ARTIFACT"
    fi
    if [ -n "$FRONTEND_ARTIFACT" ] ; then
	rm "$FRONTEND_ARTIFACT"
    fi
}

backend_wipe() {
    dropdb -h "$ROOMBAHT_DB_HOST" -U postgres "$ROOMBAHT_DB"
}

backend_migrate() {
    if ! psql -h "$ROOMBAHT_DB_HOST" -U postgres -l | grep -q "$ROOMBAHT_DB" ; then
	createdb -h "$ROOMBAHT_DB_HOST" -U postgres "$ROOMBAHT_DB"
    fi
    systemctl stop roombaht
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" migrate
    systemctl start roombaht
}

backend_venv() {
    LAST_DEPLOY="$(find /opt -name 'roombaht-backend-*' -type d | sort | tail -n 1)"
    if [ -d "${LAST_DEPLOY}/venv" ] ; then
	sudo -u roombaht -- cp -r "${LAST_DEPLOY}/venv" "${BACKEND_DIR}/venv"
    fi
    sudo -u roombaht -- bash -c "test -d ${BACKEND_DIR}/venv || ( mkdir ${BACKEND_DIR}/venv && virtualenv -p python3 ${BACKEND_DIR}/venv ) && ${BACKEND_DIR}/venv/bin/python3 -m pip install --upgrade pip"
    sudo -u roombaht -- bash -c "${BACKEND_DIR}/venv/bin/pip install -r ${BACKEND_DIR}/requirements.txt --upgrade"
}

backend_deploy() {
    BACKEND_ARTIFACT="/tmp/roombaht-backend.tgz"
    BACKEND_DIR="/opt/roombaht-backend"
    # keep some archives for rollback
    if [ -d "$BACKEND_DIR" ] ; then
	mv "$BACKEND_DIR" "${BACKEND_DIR}-${NOW}"
	for old in `find /opt -name 'roombaht-backend-*' -type d | sort | head -n "-${OLD_RELEASES}"` ; do
	    rm -rf "$old"
	done
    fi

    tar -C "/opt" -xzvf "$BACKEND_ARTIFACT"
    chown -R roombaht: "$BACKEND_DIR"
    chmod -R o-rwx "$BACKEND_DIR"
}

backend_config() {
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
	"${BACKEND_DIR}/config/roombaht-systemd.conf" \
	> "/etc/systemd/system/roombaht.service"
    chmod o-rwx "/etc/systemd/system/roombaht.service"
    systemctl daemon-reload
}

frontend_deploy() {
    FRONTEND_ARTIFACT="/tmp/roombaht-frontend.tgz"
    FRONTEND_DIR="/opt/roombaht-frontend"
    # load the frontend
    if [ -d "$FRONTEND_DIR" ] ; then
	mv "$FRONTEND_DIR" "${FRONTEND_DIR}-${NOW}"
	for old in `find /opt -name 'roombaht-frontend-*' -type d | sort | head -n "-${OLD_RELEASES}"` ; do
	    rm -rf "$old"
	done
    fi
    tar -C /opt -xzvf "$FRONTEND_ARTIFACT"
    chown -R roombaht: "$FRONTEND_DIR"
}

nginx_config() {
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
}

[ -e "$ENV_FILE" ] || problems "unable to find env file"

trap cleanup EXIT

[ "$#" -ge 1 ] || problems "invalid args"
ACTION="$1"
shift
source "$ENV_FILE"
export PGPASSWORD="$ROOMBAHT_DB_PASSWORD"

if [ "$ACTION" == "init" ] ; then
    ROOM_FILE="$1"
    STAFF_FILE="$2"
    shift 2
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" "create_rooms" "${ROOM_FILE}" --hotel ballys
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" "create_staff" "${STAFF_FILE}"
elif [ "$ACTION" == "clone_db" ] ; then
    if [ "$ROOMBAHT_DB" == "roombaht" ] ; then
	problems "can't clone prod to prod"
    fi
    SOURCE_DB="roombaht"
    while getopts "d:" arg; do
	case $arg in
	    d)
		SOURCE_DB="$OPTARG"
		;;
	    *)
		problems "Unknown option passed to clone"
		;;
	esac
    done
    if psql -h "$ROOMBAHT_DB_HOST" -U postgres -l | grep -q "$ROOMBAHT_DB" ; then
	dropdb -h "$ROOMBAHT_DB_HOST" -U postgres "$ROOMBAHT_DB"
    fi
    createdb -h "$ROOMBAHT_DB_HOST" -U postgres -T "$SOURCE_DB" "$ROOMBAHT_DB"
elif [ "$ACTION" == "wipe" ] ; then
    backend_wipe
    backend_migrate
elif [ "$ACTION" == "manage" ] ; then
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" $*
elif [ "$ACTION" == "deploy" ] ; then
    backend_venv
    backend_deploy
    backend_config
    backend_migrate
    frontend_deploy
    nginx_config
else
    echo "invalid args"

fi
