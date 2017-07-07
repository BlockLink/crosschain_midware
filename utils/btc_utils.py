# -*- coding: utf-8 -*-
import requests
from base64 import encodestring

def btc_request(method,args):
    url = "http://127.0.0.1:60011/"
    user = 'a'
    passwd = 'b'
    basestr = encodestring('%s:%s' % (user,passwd))[:-1]
    args_str = ''.join(['[', ','.join(['"' + str(arg) + '"' for arg in args]), ']'])
    payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}"%(method,args_str)
    headers = {
        'content-type': "text/plain",
        'authorization': "Basic %s"%(basestr),
        'cache-control': "no-cache",
        }
    response = requests.request("POST", url, data=payload, headers=headers)
    print(response.text)
def btc_create_address():
    btc_request("getnewaddress",[])
def get_account_list_btc_address():
    btc_request("getaddressesbyaccount",[""])
def btc_collect_money(Address):
    pass