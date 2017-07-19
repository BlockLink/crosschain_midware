#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'

import logging
from config import config

conf = config['development']

# DB configure
MONGO_HOST = conf.MONGO_HOST
MONGO_PORT = conf.MONGO_PORT
MONGO_NAME = conf.MONGO_NAME
MONGO_USER = conf.MONGO_USER
MONGO_PASS = conf.MONGO_PASS
DB_POOL_SIZE = 10
CONNECT_TIMEOUT = 50

# SYNC configure
SYNC_BLOCK_PER_ROUND = 10000

# HTTP configure
REFRESH_STAT_POST_URL = "http://52.80.29.33:8000/api"
REFRESH_STAT_POST_DATA = ''' { "jsonrpc": "2.0", "method": "Statistic.Maintain", "params": [], "id": "1" } '''

# LOG configure
LOG_LEVEL = logging.DEBUG
LOG_FILENAME = "btc_data_collector.log"

BTC_URL = conf.BTC_HOST
BTC_PORT = conf.BTC_PORT
