# -*- coding: utf-8 -*-

from config import config
from .logging_config import logger
from flask import Flask
from flask_jsonrpc import JSONRPC
from pymongo import MongoClient
import os

App = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
Jsonrpc = JSONRPC(App, '/api', enable_web_browsable_api=True)

App.config.from_object(config['development'])   # 载入配置文件


Client = MongoClient(App.config['MONGO_HOST'], App.config['MONGO_PORT'])


Client[App.config['MONGO_NAME']].authenticate(App.config['MONGO_USER'], App.config['MONGO_PASS'])

Db = Client[App.config['MONGO_NAME']]

# config_info = config.config
