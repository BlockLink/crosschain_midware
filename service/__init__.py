# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

import os
from config import logger
from flask import Flask
from config import config_info
from pymongo import MongoClient
from mongoengine import connect
from flask_jsonrpc import JSONRPC


logger.info('hello')

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

app.config.from_object(config_info['development'])   # 载入配置文件

client = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
db = client[app.config['MONGO_NAME']]

# connect(db=app.config['MONGO_NAME'], host=app.config['MONGO_HOST'], port=app.config['MONGO_PORT'])

from service import apis
