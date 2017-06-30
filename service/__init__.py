# -*- coding: utf-8 -*-

import os
from config import logger
from flask import Flask
from config import config
from flask_jsonrpc import JSONRPC
from flask_admin import Admin


logger.info('hello')

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))

admin = Admin(app, name=u'区块链查询平台', template_mode='bootstrap3')
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

app.config.from_object(config['development'])   # 载入配置文件


from service import apis
