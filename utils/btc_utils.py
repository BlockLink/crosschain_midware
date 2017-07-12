# -*- coding: utf-8 -*-
import requests
from base64 import encodestring
import json
from datetime import datetime
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
def btc_create_address(db):
    resp = btc_request("getnewaddress",["btc_test"])
    address = resp["result"]
    mongo_data = db.find_one({"chainId":"btc","address":address})
    if mongo_data == None:
        db.insert({"chainId":"btc","address":address,"createTime":datetime.now()})
    else:
        db.update({"chainId":"btc","address":address})

def btc_create_withdraw_address():
    btc_request("getnewaddress",["btc_withdraw_test"])
def btc_withdraw_to_address(amount,address):
    rep = btc_request("getbalance",["btc_withdraw_test"])
    balance = rep["result"]
    if balance <= amount:
        raise Exception("Amount error")
    params = []
    params.append("btc_test")
    params.append(address)
    params.append(amount)
    #print(params)
    btc_request("sendfrom",params)
def get_account_list_btc_address():
    btc_request("getaddressesbyaccount",["btc_test"])
def btc_collect_money(Address):
    rep = btc_request("getbalance",["btc_test"])
    balance = rep["result"]
    params = []
    params.append("btc_test")
    params.append(Address)
    params.append(balance-1)
    #print(params)
    btc_request("sendfrom",params)
def btc_withdraw_info():
    pass
#btc_collect_money("1ERjyPUWpDH7mLmAHZzwCJ6jsn4tyHfj2Y")