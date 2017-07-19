#!/bin/bash

docker-compose build
docker-compose down
docker-compose up -d chaindb
docker exec -it chaincommonapi_chaindb_1 mongo mgmt/init_db.js
docker-compose up -d chain_midware

