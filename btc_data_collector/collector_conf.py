#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'

import logging
import os

class DevelopmentConfig():
    # DB configure
    DB_POOL_SIZE = 10
    CONNECT_TIMEOUT = 50
    MONGO_HOST = '192.168.1.123'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'

    # LOG configure
    LOG_LEVEL = logging.DEBUG
    LOG_FORMAT = '%(asctime)-15s %(levelname)s %(funcName)s %(message)s'
    LOG_FILENAME = "btc_data_collector.log"

    # SYNC configure
    SYNC_BLOCK_PER_ROUND = 10000

    class BTC:
        RPC_HOST = '192.168.1.123'
        RPC_PORT = 60012


config = DevelopmentConfig



