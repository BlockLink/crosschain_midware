# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger

@jsonrpc.method('App.index')
def index():
    logger.info('App.index')
    return 'Welcome to Flask JSON-RPC'

