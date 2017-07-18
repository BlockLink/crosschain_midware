# -*- coding: utf-8 -*-
import requests
from base64 import encodestring
import json
from collector_conf import BTC_URL,BTC_PORT
def btc_request(method,args):
    #url = "http://192.168.1.104:60011/"
    url = "http://%s:%s" % (BTC_URL,BTC_PORT)
    user = 'a'
    passwd = 'b'
    basestr = encodestring('%s:%s' % (user,passwd))[:-1]
    args_j = json.dumps(args)
    payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}"%(method,args_j)
    headers = {
        'content-type': "text/plain",
        'authorization': "Basic %s"%(basestr),
        'cache-control': "no-cache",
        }
    response = requests.request("POST", url, data=payload, headers=headers)
    rep = response.json()
    #print(rep)
    return rep
