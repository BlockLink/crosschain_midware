# -*- coding: utf-8 -*-

from __future__ import print_function
from . import rpc
import requests
import json
from config import config
from service import db
# from service import models

def eth_request(method, args):
    url = "http://%s:%s/rpc"%(config["development"].ETH_URL,config["development"].ETH_PORT)
    request_template = '''{"jsonrpc":"2.0","id":"1","method":"%s","params":%s}'''
    args_str = ''.join(['[', ','.join(['"' + str(arg) + '"' for arg in args]), ']'])
    data_to_send = request_template % (method, args_str)
    payload = ""
    headers = {
        'content-type': "application/x-www-form-urlencoded"
    }

    response = requests.request("POST", url, data=data_to_send, headers=headers)
    return response.text


def eth_create_address():
    address = ''
    #写入数据库待做
    result = eth_request("personal_newAccount",[config["development"].ETH_SECRET_KEY])
    print(type(result))
    json_result = json.loads(result)
    if json_result.has_key("result"):
        address = json_result["result"]
        chain_account = db.b_chain_account(chainId="eth",address=address,pubKey="")
        chain_account[""]
        return address
    return address

def get_account_list_from_wallet():
    addressList = []
    result = eth_request("personal_listAccounts", [])
    print(type(result))
    print(result)
    json_result = json.loads(result)
    if json_result.has_key("result"):
        addressList = json_result["result"]
        return addressList
    return addressList

def get_account_list_from_db():
    addressList = []

    return addressList


def eth_collect_money(mode,Address):
    #从钱包获取归账地址列表
    if mode == 1:
        accountList = get_account_list_from_wallet()
    elif mode == 2:
        accountList = get_account_list_from_db()




if __name__ == '__main__':
    get_account_list_from_wallet()

