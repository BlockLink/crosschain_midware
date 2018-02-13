#!/usr/bin/env python
# encoding: utf-8

__author__ = 'ted'

from collector_conf import config
from collect_btc_block import do_collect_app
import logging
from pymongo import MongoClient

if __name__ == '__main__':
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT, filename=config.LOG_FILENAME, filemode="a")
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    client = MongoClient(host=config.MONGO_HOST, port=config.MONGO_PORT)
    client[config.MONGO_NAME].authenticate(config.MONGO_USER, config.MONGO_PASS)
    db = client[config.MONGO_NAME]

    do_collect_app(db)
