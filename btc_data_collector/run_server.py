#!/usr/bin/env python
# encoding: utf-8

__author__ = 'ted'

from twisted.internet import reactor
from collector_conf import CollectorConfig
from collect_btc_block import BTCCoinTxCollecter
from collect_ltc_block import LTCCoinTxCollecter
from collect_ub_block import UBCoinTxCollecter
import logging
import sys
import txmongo


if __name__ == '__main__':
    config = CollectorConfig()
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT, filename=config.LOG_FILENAME, filemode="a")
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    client = txmongo.MongoConnectionPool(host=config.MONGO_HOST, port=config.MONGO_PORT, pool_size=config.DB_POOL_SIZE)
    #client = MongoClient(host=config.MONGO_HOST, port=config.MONGO_PORT)
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
    reactor.callWhenRunning(collector.do_collect_app)
    reactor.callWhenRunning(collector.flush_mongo_db)
    reactor.callWhenRunning(collector.flush_block_db)
    reactor.run()
