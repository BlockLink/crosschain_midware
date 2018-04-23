#!/bin/bash


sudo apt-get remove docker docker-engine docker.io
sudo apt-get update
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update
sudo apt-get install -y docker-ce

docker-compose build python_web
docker-compose build
docker-compose down
docker-compose up -d chaindb
docker cp mgmt/init_db.js chaincommonapi_chaindb_1:/
sleep 5
docker exec -it chaincommonapi_chaindb_1 mongo init_db.js
docker-compose up -d chain_midware

