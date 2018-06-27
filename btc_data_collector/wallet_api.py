# -*- coding: utf-8 -*-
import requests
import json
from base64 import encodestring
import logging

logging.getLogger("requests").setLevel(logging.WARNING)

class WalletApi:
    def __init__(self, name, conf):
        self.name = name
        self.config = conf

    def http_request(self, method, args):
        if self.name == 'HC':
            url = "https://%s:%s" % (self.config["host"], self.config["port"])
        else:
            url = "http://%s:%s" % (self.config["host"], self.config["port"])
        user = 'a'
        passwd = 'b'
        basestr = encodestring('%s:%s' % (user, passwd))[:-1]
        args_j = json.dumps(args)
        payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
        headers = {
            'content-type': "text/plain",
            'authorization': "Basic %s" % (basestr),
            'cache-control': "no-cache",
        }
        if self.name == "HC":
            requests.packages.urllib3.disable_warnings()
            response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        else:
            response = requests.request("POST", url, data=payload, headers=headers)
        rep = response.json()
        return rep