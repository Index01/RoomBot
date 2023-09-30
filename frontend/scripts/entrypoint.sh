#!/usr/bin/env sh

set -ex

if [ "$1" = "build" ] ; then
    cd /src
    npm install
    npm run build
else
    cd /app
    npm run start
fi
