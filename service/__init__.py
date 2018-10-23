# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

import os
from config import logger
from config import App
from config import Db
from config import Client
from config import Jsonrpc
from utils.sim_btc_utils import sim_btc_utils
from utils.hc_utils import hc_utils
logger.info('Start app...')
app = App
db = Db
client = Client
jsonrpc = Jsonrpc
sim_btc_utils_all = ["btc", "ltc", "ub"]
sim_btc_plugin = {}
for value in sim_btc_utils_all:
    upper = value.upper()
    sim_btc_config = {}
    if app.config.has_key(upper+"_HOST") and app.config.has_key(upper+"_PORT") and app.config.has_key(upper + "_FEE"):
        sim_btc_config["host"] = app.config[upper+"_HOST"]
        sim_btc_config["port"] = app.config[upper+"_PORT"]
        sim_btc_config["fee"] = app.config[upper+"_FEE"]
        sim_btc_plugin[value] = sim_btc_utils(value, sim_btc_config)
hc_config = {}
if app.config.has_key("HC_HOST") and app.config.has_key("HC_PORT") and app.config.has_key("HC_FEE"):
    hc_config["host"] = app.config["HC_HOST"]
    hc_config["port"] = app.config["HC_PORT"]
    hc_config["fee"] = app.config["HC_FEE"]
hc_plugin = hc_utils("hc", hc_config)
from service import sim_api
from service import client_api
