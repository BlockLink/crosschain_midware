# -*- coding: utf-8 -*-
import requests
from base64 import encodestring
import json
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
    print btc_request("getnewaddress",["1"])
def get_account_list_btc_address():
    btc_request("getaddressesbyaccount",["datest"])
def btc_collect_money(Address):
    rep = btc_request("getbalance",[""])
    balance = rep["result"]
    params = []
    params.append("")
    params.append(Address)
    params.append(balance-1)
    #print(params)
    btc_request("sendfrom",params)
#btc_collect_money("1ERjyPUWpDH7mLmAHZzwCJ6jsn4tyHfj2Y")