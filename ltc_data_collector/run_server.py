#!/usr/bin/env python
# encoding: utf-8

__author__ = 'ted'

from collector_conf import MONGO_HOST, MONGO_NAME, MONGO_PORT, DB_POOL_SIZE, MONGO_PASS, MONGO_USER
from collector_conf import LOG_LEVEL, LOG_FILENAME
from colloc_ltc_block import do_collect_app
import logging
from pymongo import MongoClient

if __name__ == '__main__':
    LOG_FORMAT = '%(asctime)-15s %(levelname)s %(funcName)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, filename=LOG_FILENAME, filenode="a")
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
	console.setFormatter(formatter)
	logging.getLogger('').addHandler(console)


    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    client[MONGO_NAME].authenticate(MONGO_USER, MONGO_PASS)
    db = client[MONGO_NAME]
    #db.authenticate(MONGO_USER, MONGO_PASS)

    do_collect_app(db)
