# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

import os
from config import logger
from flask import Flask
from config import config
from pymongo import MongoClient
from flask_jsonrpc import JSONRPC


logger.info('Start app...')

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

app.config.from_object(config['development'])   # 载入配置文件

client = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])

db = client[app.config['MONGO_NAME']].authenticate(app.config['MONGO_USER'],app.config['MONGO_PASS'],mechanism="SCRAM-SHA-1")


from service import apis
