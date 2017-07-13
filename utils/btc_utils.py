# -*- coding: utf-8 -*-
import requests
from base64 import encodestring
import json
from datetime import datetime
from service import db
def btc_request(method,args):
    url = "http://127.0.0.1:60011/"
    user = 'a'
    passwd = 'b'
    basestr = encodestring('%s:%s' % (user,passwd))[:-1]
    '''x = []
    for arg in args:
        x.append(arg)'''
    args_j = json.dumps(args)
    payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}"%(method,args_j)
    headers = {
        'content-type': "text/plain",
        'authorization': "Basic %s"%(basestr),
        'cache-control': "no-cache",
        }
    response = requests.request("POST", url, data=payload, headers=headers)
    rep = response.json()
    return rep
def btc_create_address():
    resp = btc_request("getnewaddress",["btc_test"])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address


def btc_create_withdraw_address():
    resp = btc_request("getnewaddress",["btc_withdraw_test"])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address
def btc_collect_money():
    resp = btc_request("settxfee",[0.0004])
    if resp["result"] == None:
        raise Exception("settxfee error")
    sweep_address = db.b_config.find_one({"key":"btcsweepaddress"})["value"]
    if sweep_address == None:
        raise Exception("find sweep address error")
    safe_block = db.b_config.find_one({"key":"btcsafeblock"})["value"]
    resp = btc_request("getbalance",["btc_test"],safe_block)
    if resp["result"] == None:
        raise Exception("getbalance error")
    balance = resp["result"]
    if balance - 0.0004 <= 0:
        raise Exception("balance is not enough error")
    params = ["btc_test",sweep_address ,balance-0.0004]
    resp = btc_request("sendfrom",params)
    if resp["result"] == None:
        return ""
    return resp["result"]

def btc_withdraw_to_address(amount,address):
    rep = btc_request("getbalance",["btc_withdraw_test"])
    balance = rep["result"]
    if balance <= amount:
        raise Exception("Amount error")
    params = ["btc_withdraw_test",address,amount]
    #print(params)
    btc_request("sendfrom",params)

def get_account_list_btc_address():
    btc_request("getaddressesbyaccount",["btc_test"])

def btc_backup_wallet():
    btc_request("backupwallet",[])
def btc_withdraw_info():

    pass
#btc_collect_money("1ERjyPUWpDH7mLmAHZzwCJ6jsn4tyHfj2Y")