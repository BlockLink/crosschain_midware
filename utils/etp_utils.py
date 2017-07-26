# -*- coding: utf-8 -*-

# from __future__ import print_function
import requests
import json
from config import config
import sys
import shutil
import os
from math import pow,floor
import time
from service import logger
import traceback

temp_config = config["hzk"]

def etp_request(method, args):
    url = "http://%s:%s/rpc" % (temp_config.ETP_URL, temp_config.ETP_PORT)
    request_template = '''{"jsonrpc":"2.0","id":"1","method":"%s","params":%s}'''
    args_str = json.dumps(args)
    data_to_send = request_template % (method, args_str)
    print data_to_send

    payload = ""
    headers = {
        'content-type': "application/x-www-form-urlencoded"
    }

    response = requests.request("POST", url, data=data_to_send, headers=headers)
    return response.text

#创建用户
def etp_create_address():
    address = ''
    data = {}
    # 写入数据库待做
    result = etp_request("getnewaddress", ['etp_test','etp_test'])
    if result[0] != 't' and result[0] != 'M':
        return None
    address = result
    return address

def number(num) :
    num=int(num)
    sum=1
    while num >0 :
        sum = sum * 10
        num -= 1
    return sum


def etp_get_addr_balance(addr):
    result = etp_request("fetch-balance", [addr])
    json_result = json.loads(result)
    balance={}
    balance['etp'] = float(json_result.get('balance').get('confirmed'))/float(100000000)

    result = etp_request("getaddressasset",[addr])
    json_result = json.loads(result)
    assets = json_result.get('assets')

    for asset in assets :
        balance[asset.get('symbol')] = float(asset.get('quantity'))/float(number(asset.get('decimal_number')))
    return balance

def etp_backup_wallet() :
    pass

def etp_collect_money(address):
    try:
        # 发送其他智能资产
        resp = etp_request("getbalance", ["etp_test", "etp_test"])
        balance = 0
        try:
            balance = int(json.loads(resp).get("total-confirmed"))
            if int(balance) <= 10000:
               raise Exception("balance is not enough error")
        except:
            return
        resp = etp_request("getaccountasset", ["etp_test", "etp_test"])
        assets = json.loads(resp)
        Fee=10000
        if assets.get("assets") is not None:
            for asset in assets:
                symbol = asset.get("symbol")
                quantity = asset.get("quantity")
                result = etp_request("sendasset",["etp_test","etp_test",address,symbol,int(quantity)])
                ret = json.loads(result)
                if ret.get("transaction") is not None :
                    Fee += 10000
        params = ["etp_test", "etp_test", address, balance - Fee]
        resp = etp_request("send", params)
        if json.loads(resp).get("transactions") is None:
            raise Exception("send ETP to %s failed." % address)
        return {"from_addr": "etp_test", "to_addr": address, "amount": float(balance - Fee)/float(100000000),
                        "trx_id": resp["result"]},None
    except Exception as e:
        logger.info(traceback.format_exc())
        return None, e.message

def etp_create_withdraw_address():
    resp = etp_request("getnewaddress", ["etp_withdraw_test"])
    address = ""
    if resp[0] != 'M' :
        return None
    address = resp
    return address
#只限于etp，不包含智能资产
def etp_withdraw_address(address, amount) :
    try:
        result_data = {}
        result_data["errdata"] = []
        result_data["data"] = []
        resp = etp_request("getbalance", ["etp_withdraw_test","etp_withdraw_test"])
        try:
            amount = amount * float(100000000)
            balance = int(json.loads(resp).get("total-confirmed"))
            if int(balance) <= amount:
               raise Exception("balance is not enough error")
        except:
            return
        params = ["etp_withdraw_test","etp_withdraw_test", address, amount]
        resp = etp_request("send", params)
        if json.loads(resp).get("transactions") is None:
            raise Exception("send ETP to %s failed." % address)
        return {"from_addr": "etp_test", "to_addr": address, "amount": amount / float(100000000),
                "trx_id": resp["result"]}
    except Exception, ex:
        logger.info(traceback.format_exc())
        return ""



if __name__ == '__main__':
    #print etp_get_addr_balance("MUqWtDM78aftFUnzkrtgBgUVGWLJgXxPEw")
    print etp_collect_money("MUqWtDM78aftFUnzkrtgBgUVGWLJgXxPEw")