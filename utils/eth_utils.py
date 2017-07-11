# -*- coding: utf-8 -*-

from __future__ import print_function
from . import rpc
import requests
import json
from config import config
from service import db
from datetime import datetime

temp_config = config["development"]

def eth_request(method, args):
    url = "http://%s:%s/rpc"%(config["development"].ETH_URL,temp_config.ETH_PORT)
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
    data = {}
    #写入数据库待做
    result = eth_request("personal_newAccount",[temp_config.ETH_SECRET_KEY])
    print type(result)
    json_result = json.loads(result)
    if json_result.has_key("result"):
        address = json_result["result"]
        data["address"] = address
        data["chainId"] = "eth"
        data["creatorUserId"] = 0
        data["balance"] = {"eth":0}
        data["pubKey"] = ""
        data["createTime"] = datetime.now()
        chain_account = db.b_chain_account
        chain_account.insert(data)
        return address
    return address


def eth_get_base_balance(address):

    result = eth_request("eth_getBalance", [address,"latest"])
    print result
    json_result = json.loads(result)
    amount =  long(json_result["result"],16)
    return float(amount/pow(10,18))



def get_account_list_from_wallet():
    addressList = []
    result = eth_request("personal_listAccounts", [])
    print type(result)
    print result
    json_result = json.loads(result)
    if json_result.has_key("result"):
        addressList = json_result["result"]
        return addressList
    return addressList

def get_account_list_from_db():
    addressList = []
    chain_account = db.b_chain_account
    resultData = chain_account.find({"chainId":"eth"})
    for one_data in resultData:
        print one_data
        addressList.append(one_data["address"])

    return addressList


def eth_collect_money(mode,Address):
    #从钱包获取归账地址列表
    if mode == 1:
        accountList = get_account_list_from_wallet()
    elif mode == 2:
        accountList = get_account_list_from_db()
    print accountList
    for account in accountList:
        amount = eth_get_base_balance(Address)
        print amount
        if amount > temp_config.ETH_Minimum:
            #转账给目标账户
            result = eth_request("personal_unlockAccount",[account,temp_config.ETH_SECRET_KEY])
            print result
            pass
    return






if __name__ == '__main__':
    #get_account_list_from_wallet()
    #eth_create_address()
    #get_account_list_from_db()
    eth_collect_money(2,"0x085aa94b764316d5e608335d13d926c6c6911e56")

