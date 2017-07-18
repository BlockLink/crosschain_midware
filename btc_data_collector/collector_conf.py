#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'

import logging



# DB configure
MONGO_HOST = '192.168.1.115'
MONGO_PORT = 27017
MONGO_NAME = 'chaindb'
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


BTC_URL = "192.168.1.104"
BTC_PORT = 60011

