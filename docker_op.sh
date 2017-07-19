#!/bin/bash

docker-compose build
docker-compose down
docker-compose up -d chaindb
docker cp mgmt/init_db.js chaincommonapi_chaindb_1:/
sleep 5
docker exec -it chaincommonapi_chaindb_1 mongo init_db.js
docker-compose up -d chain_midware

