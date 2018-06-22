# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

import os
from config import logger
from flask import Flask
from config import config
from pymongo import MongoClient
from flask_jsonrpc import JSONRPC
from utils.sim_btc_utils import sim_btc_utils
from utils.hc_utils import hc_utils
logger.info('Start app...')

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

app.config.from_object(config['development'])   # 载入配置文件


client = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])


client[app.config['MONGO_NAME']].authenticate(app.config['MONGO_USER'], app.config['MONGO_PASS'])

db = client[app.config['MONGO_NAME']]
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
