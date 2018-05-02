#!/usr/bin/env python
# encoding: utf-8

__author__ = 'ted'

from collector_conf import CollectorConfig
from collect_btc_block import BTCCoinTxCollecter
from collect_ltc_block import LTCCoinTxCollecter
from collect_ub_block import UBCoinTxCollecter
import logging
import sys
from pymongo import MongoClient

if __name__ == '__main__':
    config = CollectorConfig()
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT, filename=config.LOG_FILENAME, filemode="a")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    client = MongoClient(host=config.MONGO_HOST, port=config.MONGO_PORT)
    client[config.MONGO_NAME].authenticate(config.MONGO_USER, config.MONGO_PASS)
    db = client[config.MONGO_NAME]

    # collector = BTCCoinTxCollecter(db)
    if not len(sys.argv) == 2:
        print "Please indicate which type of coin tx to collect [btc|ltc]"
        exit(1)
    elif sys.argv[1] == "btc":
        collector = BTCCoinTxCollecter(db)
    elif sys.argv[1] == "ltc":
        collector = LTCCoinTxCollecter(db)
    elif sys.argv[1] == "ub":
        collector = UBCoinTxCollecter(db)
    else:
        print "Please indicate correct type of coin tx to collect [btc|ltc]"
        exit(1)

    collector.do_collect_app()
