#!/usr/bin/env bash

PACKAGES=(aptitude nginx screen python3 virtualenv certbot python3-certbot-nginx postgresql-client htop iftop build-essential python3-dev libpq-dev jq)

set -e

problems() {
    2>&1 echo "Error: $*"
    exit 1
}

add_user() {
    local A_USER="$1"
    if [ $# == 2 ] ; then
	local GITHUB="$2"
    fi
    local SSH_DIR="/home/${A_USER}/.ssh"
    local SSH_KEYS="${SSH_DIR}/authorized_keys"
    if ! id "$1" &> /dev/null ; then
	adduser --disabled-password --gecos "$A_USER" "$A_USER"
    fi
    if [ -n "$GITHUB" ] ; then
	if [ ! -d "$SSH_DIR" ] ; then
	    mkdir -p "$SSH_DIR"
	    chown "${A_USER}:" "$SSH_DIR"
	    chmod og-rwx "$SSH_DIR"
	fi
	curl -s -o "$SSH_KEYS" "https://github.com/${GITHUB}.keys" || \
	    problems "unable to fetch keys for ${GITHUB}"
	chmod og-rwx "$SSH_KEYS"
	chown "${A_USER}:" "$SSH_KEYS"
    fi
}

sudo_user() {
    local A_USER="$1"
    local SUDO_FILE="/etc/sudoers.d/20-roombaht"
    if [ -e "$SUDO_FILE" ] ; then
	if grep -q "$A_USER" "$SUDO_FILE" ; then
	    return
	fi
    else
	echo "# autogenerated with love by janky shell scripts" >> "$SUDO_FILE"
    fi
    echo "${A_USER} ALL=(ALL) NOPASSWD:ALL" >> "$SUDO_FILE"
}

lock_user() {
    local A_USER="$1"
    usermod -s /usr/sbin/nologin "$A_USER"
}

os_freshen() {
    apt-get update
    apt-get upgrade -y
    apt-get install -y "${PACKAGES[@]}"
    pip install --upgrade awscli
}

os_freshen

add_user gadget otakup0pe
add_user index Index01
add_user roombaht
lock_user ubuntu

sudo_user gadget
sudo_user index
