#!/usr/bin/env bash

set -e

BACKEND_ARTIFACT="/tmp/roombaht-backend.tgz"
FRONTEND_ARTIFACT="/tmp/roombaht-frontend.tgz"

BACKEND_DIR="/opt/roombaht-backend"
FRONTEND_DIR="/opt/roombaht-frontend"

NOW="$(date '+%m%d%Y-%H%M')"
OLD_RELEASES=5

if [ -z "$ENV_FILE" ] ; then
    ENV_FILE="/tmp/secrets.env"
fi


problems() {
    2>&1 echo "Error: $*"
    exit 1
}

cleanup() {
    if [ -n "$ENV_FILE" ] && [ -e "$ENV_FILE" ] ; then
	rm "$ENV_FILE"
    fi
    if [ -n "$BALLYS_FILE" ] && [ -e "$BALLYS_FILE" ] ; then
	rm "$BALLYS_FILE"
    fi
    if [ -n "$HARDROCK_FILE" ] && [ -e "$HARDROCK_FILE" ] ; then
	rm "$HARDROCK_FILE"
    fi
    if [ -n "$STAFF_FILE" ] && [ -e "$STAFF_FILE" ]; then
	rm "$STAFF_FILE"
    fi
    if [ -n "$BACKEND_ARTIFACT" ] && [ -e "$BACKEND_ARTIFACT" ]; then
	rm "$BACKEND_ARTIFACT"
    fi
    if [ -n "$FRONTEND_ARTIFACT" ] && [ -e "$FRONTEND_ARTIFACT" ]; then
	rm "$FRONTEND_ARTIFACT"
    fi
}

# determine db connection details
db_connection() {
    ACCOUNT_ID="$(aws sts get-caller-identity --query 'Account' --output text 2> /dev/null)"
    if [ -z "$ACCOUNT_ID" ] ; then
	problems "Unable to look up AWS Account ID"
    fi
    REGION="$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone 2> /dev/null)"
    REGION="$(sed 's/[a-z]$//' <<< "$REGION")"
    if [ -z "$REGION" ] ; then
	problems "Unable to look up AWS Region"
    fi
    RDS_ARN="arn:aws:rds:${REGION}:${ACCOUNT_ID}:db:roombaht"
    ROOMBAHT_DB_HOST="$(aws rds describe-db-instances --region "${REGION}" --db-instance-identifier "${RDS_ARN}" --query 'DBInstances[0].Endpoint.Address' --output text 2> /dev/null)"
    if [ -z "$ROOMBAHT_DB_HOST" ] ; then
	problems "Unable to look up RDS Address"
    fi
    SECRET_ARN="$(aws rds describe-db-instances --region "${REGION}" --db-instance-identifier "${RDS_ARN}" --query 'DBInstances[0].MasterUserSecret.SecretArn' --output text 2> /dev/null)"
    if [ -z "$SECRET_ARN" ] ; then
	problems "Unable to look up RDS Auth ARN"
    fi
    PGPASSWORD="$(aws secretsmanager get-secret-value --secret-id "${SECRET_ARN}" --region "${REGION}" --query SecretString --output text | jq -Mr '.password')"
    if [ -z "$PGPASSWORD" ] ; then
	problems "Unable to look up RDS Password"
    fi
    export PGPASSWORD
}

# wipe the database if present
db_wipe() {
    if [ "$(psql -h "$ROOMBAHT_DB_HOST" -U root -Atc "select 1 from pg_database where datname='${ROOMBAHT_DB}'" postgres 2> /dev/null)" == "1" ] ; then
	dropdb -h "$ROOMBAHT_DB_HOST" -U root "$ROOMBAHT_DB"
    fi
}

# clone production into a new db
db_clone() {
    createdb -h "$ROOMBAHT_DB_HOST" -U root -T "$SOURCE_DB" "$ROOMBAHT_DB"
}

# clone db into snapshot
db_snapshot() {
    local DEST_DB="${ROOMBAHT_DB}-${NOW}"
    createdb -h "$ROOMBAHT_DB_HOST" -U root -T "$ROOMBAHT_DB" "$DEST_DB"
}

# create database if needed and then issue migrations
db_migrate() {
    if [ -z "$(psql -h "$ROOMBAHT_DB_HOST" -U root -Atc "select 1 from pg_database where datname='${ROOMBAHT_DB}'" postgres 2> /dev/null)" ] ; then
	createdb -h "$ROOMBAHT_DB_HOST" -U root "$ROOMBAHT_DB"
    fi
    systemctl stop roombaht
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" migrate
    systemctl start roombaht
}

backend_venv() {
    LAST_DEPLOY="$(find /opt -name 'roombaht-backend-*' -type d | sort | tail -n 1)"
    if [ -d "${LAST_DEPLOY}/venv" ] ; then
	find "${LAST_DEPLOY}/venv" -name \*.pyc | xargs --no-run-if-empty rm
	sudo -u roombaht -- cp -r "${LAST_DEPLOY}/venv" "${BACKEND_DIR}/"
	chown -R roombaht: "${BACKEND_DIR}/venv"
    fi
    sudo -u roombaht -- bash -c "test -d ${BACKEND_DIR}/venv || ( mkdir ${BACKEND_DIR}/venv && virtualenv -p python3 ${BACKEND_DIR}/venv ) && ${BACKEND_DIR}/venv/bin/python3 -m pip install --upgrade pip"
    sudo -u roombaht -- bash -c "${BACKEND_DIR}/venv/bin/pip install -r ${BACKEND_DIR}/requirements.txt --upgrade"
}

backend_deploy() {
    # keep some archives for rollback
    BACKEND_OLD="${BACKEND_DIR}-${NOW}"
    if [ -d "$BACKEND_DIR" ] ; then
	mv "$BACKEND_DIR" "$BACKEND_OLD"
	for old in `find /opt -name 'roombaht-backend-*' -type d | sort | head -n "-${OLD_RELEASES}"` ; do
	    rm -rf "$old"
	done
    fi
    tar -C "/opt" -xzvf "$BACKEND_ARTIFACT"
    if [ -d "${BACKEND_OLD}/venv" ] ; then
	cp -r "${BACKEND_OLD}/venv" "${BACKEND_DIR}/venv"
    fi
    chown -R roombaht: "$BACKEND_DIR"
    chmod -R o-rwx "$BACKEND_DIR"
}

# update backend config and cron, which is kinda config
backend_config() {
    sed -e "s/@SECRET_KEY@/${ROOMBAHT_DJANGO_SECRET_KEY}/" \
	-e "s/@EMAIL_HOST_USER@/${ROOMBAHT_EMAIL_HOST_USER}/" \
	-e "s/@EMAIL_HOST_PASSWORD@/${ROOMBAHT_EMAIL_HOST_PASSWORD}/" \
	-e "s/@DB_NAME@/${ROOMBAHT_DB}/" \
	-e "s/@SEND_MAIL@/${ROOMBAHT_SEND_MAIL}/" \
	-e "s%@TEMP@%${ROOMBAHT_TMP}%" \
	-e "s/@JWT_KEY@/${ROOMBAHT_JWT_KEY}/" \
	-e "s/@HOST@/${ROOMBAHT_HOST}/" \
	-e "s/@LOGLEVEL@/${ROOMBAHT_LOGLEVEL}"/ \
	-e "s/@SEND_ONBOARDING@/${ROOMBAHT_SEND_ONBOARDING}/" \
	-e "s/@IGNORE_TRANSACTIONS@/${ROOMBAHT_IGNORE_TRANSACTIONS}/" \
	-e "s/@DEV_MAIL@/${ROOMBAHT_DEV_MAIL}/" \
	-e "s/@GUEST_HOTELS@/${ROOMBAHT_GUEST_HOTELS}/" \
	-e "s/@SWAPS_ENABLED@/${ROOMBAHT_SWAPS_ENABLED}/" \
	-e "s/@FEATURES@/${ROOMBAHT_FEATURES}/" \
	-e "s/@URL_PORT@/${ROOMBAHT_URL_PORT}/" \
	-e "s/@URL_SCHEMA@/${ROOMBAHT_URL_SCHEMA}/" \
	"${BACKEND_DIR}/config/roombaht-systemd.conf" \
	> "/etc/systemd/system/roombaht.service"
    chmod o-rwx "/etc/systemd/system/roombaht.service"
    systemctl daemon-reload
    sed -e "s/@SECRET_KEY@/${ROOMBAHT_DJANGO_SECRET_KEY}/" \
	-e "s/@EMAIL_HOST_USER@/${ROOMBAHT_EMAIL_HOST_USER}/" \
	-e "s/@EMAIL_HOST_PASSWORD@/${ROOMBAHT_EMAIL_HOST_PASSWORD}/" \
	-e "s/@DB_NAME@/${ROOMBAHT_DB}/" \
	-e "s/@SEND_MAIL@/${ROOMBAHT_SEND_MAIL}/" \
	-e "s%@TEMP@%${ROOMBAHT_TMP}%" \
	-e "s/@JWT_KEY@/${ROOMBAHT_JWT_KEY}/" \
	-e "s/@HOST@/${ROOMBAHT_HOST}/" \
	-e "s/@LOGLEVEL@/${ROOMBAHT_LOGLEVEL}"/ \
	-e "s/@SEND_ONBOARDING@/${ROOMBAHT_SEND_ONBOARDING}/" \
	-e "s/@IGNORE_TRANSACTIONS@/${ROOMBAHT_IGNORE_TRANSACTIONS}/" \
	-e "s/@ONBOARDING_BATCH@/${ROOMBAHT_ONBOARDING_BATCH}/" \
	-e "s/@DEV_MAIL@/${ROOMBAHT_DEV_MAIL}/" \
	-e "s/@SWAPS_ENABLED@/${ROOMBAHT_SWAPS_ENABLED}/" \
	-e "s/@URL_PORT@/${ROOMBAHT_URL_PORT}/" \
	-e "s/@URL_SCHEMA@/${ROOMBAHT_URL_SCHEMA}/" \
	"${BACKEND_DIR}/scripts/roombaht-oob.sh" \
	> "/opt/roombaht-backend/scripts/roombaht-oob"
    chmod 0770 "/opt/roombaht-backend/scripts/roombaht-oob"
    chown roombaht: "/opt/roombaht-backend/scripts/roombaht-oob"
    cp /opt/roombaht-backend/scripts/roombaht-oob.cron \
       /etc/cron.d/roombaht-oob
}

frontend_deploy() {
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
    local CERTPATH="/etc/letsencrypt/live/${ROOMBAHT_HOST}"
    if [ ! -d "$CERTPATH" ] ; then
	certbot certonly --nginx \
		-d "$ROOMBAHT_HOST" \
		--email "$ROOMBAHT_TECH_EMAIL" \
		--agree-tos --no-eff-email
    fi
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
# shellcheck disable=SC1090
source "$ENV_FILE"

if [ "$ACTION" == "load_staff" ] ; then
    STAFF_FILE="/tmp/${1}"
    shift
    if [ ! -e "$STAFF_FILE" ] ; then
	problems "Unable to load staff from ${STAFF_FILE}"
    fi
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" "create_staff" "${STAFF_FILE}"
elif [ "$ACTION" == "load_rooms" ] ; then
    HOTEL="$1"
    ROOM_FILE="/tmp/${2}"
    shift
    if [ ! -e "$ROOM_FILE" ] ; then
	problems "Unable to load rooms from ${ROOM_FILE}"
    fi
    db_connection
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" \
	create_rooms "$ROOM_FILE" --hotel "$HOTEL" --preserve
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
    db_connection
    db_wipe
    db_clone
elif [ "$ACTION" == "wipe" ] ; then
    db_connection
    db_wipe
    db_migrate
elif [ "$ACTION" == "snapshot" ] ; then
    db_connection
    db_snapshot
elif [ "$ACTION" == "manage" ] ; then
    "/opt/roombaht-backend/venv/bin/python3" \
	"/opt/roombaht-backend/manage.py" $*
elif [ "$ACTION" == "deploy" ] ; then
    frontend_deploy
    backend_deploy
    backend_venv
    backend_config
    db_connection
    db_migrate
    nginx_config
elif [ "$ACTION" == "quick_deploy" ] ; then
    backend_deploy
    backend_config
    frontend_deploy
else
    echo "invalid args"
fi
