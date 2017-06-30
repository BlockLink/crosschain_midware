# -*- coding: utf-8 -*-

import os
from config import logger
from flask import Flask
from config import config
from flask_jsonrpc import JSONRPC


logger.info('hello')

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))

jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

app.config.from_object(config['development'])   # 载入配置文件


from service import apis
