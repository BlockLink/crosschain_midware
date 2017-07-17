# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime
from collector_conf import ETH_PORT,ETH_URL


def eth_request(method, args):
    url = "http://%s:%s/rpc"%(ETH_URL,ETH_PORT)
    request_template = '''{"jsonrpc":"2.0","id":"1","method":"%s","params":%s}'''
    args_j = json.dumps(args)

    data_to_send = request_template % (method, args_j)
    headers = {
        'content-type': "application/x-www-form-urlencoded"
    }

    response = requests.request("POST", url, data=data_to_send, headers=headers)
    return response.text







if __name__ == '__main__':
    print eth_request("eth_getCode",["0x5901deb2c898d5dbe5923e05e510e95968a35067","latest"])
