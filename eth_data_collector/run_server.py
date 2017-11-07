#!/usr/bin/env python
# encoding: utf-8

__author__ = 'sunny'

from twisted.internet import reactor
from collector_conf import MONGO_HOST, MONGO_NAME, MONGO_PORT, DB_POOL_SIZE, MONGO_USER, MONGO_PASS
from collector_conf import LOG_LEVEL, LOG_FILENAME
from collector_app import do_collect_app
import logging
#from pymongo import MongoClient
import txmongo

if __name__ == '__main__':
    LOG_FORMAT = '%(asctime)-15s %(levelname)s %(funcName)s %(message)s'
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, filename=LOG_FILENAME, filenode="a")
    client = txmongo.MongoConnectionPool(host=MONGO_HOST, port=MONGO_PORT,pool_size=DB_POOL_SIZE)
    #client = txmongo.MongoConnection(host=MONGO_HOST, port=MONGO_PORT)
    client[MONGO_NAME].authenticate(MONGO_USER, MONGO_PASS)

    db = client[MONGO_NAME]

    reactor.callWhenRunning(do_collect_app, db)
    reactor.run()
    # db.authenticate(MONGO_USER, MONGO_PASS)

    #do_collect_app(db)
