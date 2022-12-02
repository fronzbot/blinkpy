#!/usr/bin/env bash
# bash run.sh [username] [password]

if [ "$#" -ne 2 ]; then
    echo ""
    echo "ERROR: Requries Blink username and password as arguments."
    echo "bash run.sh [username] [password]"
    echo ""
    exit 1
fi

#set -ex
USER=fronzbot
CONTAINER=blinkpy
CONFIG=$HOME/blinkpy_media
USERNAME=$1
PASSWORD=$2
CREDSDIR=$HOME/.blinkapp

mkdir -p $CONFIG
mkdir -p $CREDSDIR

result=$(docker images -q $CONTAINER)
if [ $result ]; then
  echo "Removing ${result}"
  docker rm -f $CONTAINER
else
  echo "${CONTAINER} not found"
fi

docker rm -f $CONTAINER
docker run -it --name ${CONTAINER} \
    -v $CONFIG:/media \
    -v $CREDSDIR:/blink_creds \
    -e USERNAME=${USERNAME} \
    -e PASSWORD=${PASSWORD} \
    -e CREDFILE=${CREDFILE} \
    -e TIMEDELTA=${TIMEDELTA} \
    $USER/$CONTAINER \
    /bin/bash

