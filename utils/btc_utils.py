# -*- coding: utf-8 -*-

from __future__ import print_function
from . import rpc
import requests
import json
from config import config
from service import db
# from service import models
def btc_request(method,args):
    btc_conn = rpc.create_btc_rpc_client()
    return btc_conn.request(method,args)
    pass
def btc_create_address():
    btc_request("getnewaddress","")
    pass
def get_account_list_btc_address():
    btc_request("getaddressesbyaccount","")
    pass
def btc_collect_money(Address):
    pass
