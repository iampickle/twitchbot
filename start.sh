#!/bin/bash
clear
cd /home/tbot/twitchbot/

set -a
source <(cat .env | \
    sed -e '/^#/d;/^\s*$/d' -e "s/'/'\\\''/g" -e "s/=\(.*\)/='\1'/g" -e "s/-/_/g")
set +a

cd ./
pwd
source $conda_path tbot
python ./main.py
