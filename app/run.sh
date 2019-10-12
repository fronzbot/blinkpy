#!/bin/bash
# bash run.sh [username] [password]

if [ "$#" -ne 2 ]; then
    echo ""
    echo "ERROR: Requries Blink username and password as arguments."
    echo "bash run.sh [username] [password]"
    echo ""
    exit 1
fi

set -ex
USER=fronzbot
IMAGE=blinkpy
CONFIG=$HOME/blinkpy_media
USERNAME=$1
PASSWORD=$2

mkdir -p $CONFIG

result=$(docker images -q $IMAGE)
if [ $result ]; then
    docker rm $IMAGE
fi
docker run -it --name ${IMAGE} \
    -v $CONFIG:/media \
    -e USERNAME=${USERNAME} \
    -e PASSWORD=${PASSWORD} \
    $USER/$IMAGE \
    /bin/bash

