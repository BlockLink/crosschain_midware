#!/usr/bin/env python
# encoding: utf-8

__author__ = 'sunny'


from collector_conf import MONGO_HOST,MONGO_NAME,MONGO_PORT,MONGO_PASS,MONGO_USER
from collector_conf import LOG_LEVEL, LOG_FILENAME
from collector_app import do_collect_app
import logging
from pymongo import MongoClient


if __name__ == '__main__':
    LOG_FORMAT = '%(asctime)-15s %(levelname)s %(funcName)s %(message)s'
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, filename=LOG_FILENAME, filenode="a")

    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    client[MONGO_NAME].authenticate(MONGO_USER, MONGO_PASS)


    db = client[MONGO_NAME]

    do_collect_app(db)