# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime
from collector_conf import ETH_PORT, ETH_URL
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.client import Agent, readBody
from bytesprod import BytesProducer

def eth_request(method, args):
    url = "http://%s:%s/rpc" % (ETH_URL, ETH_PORT)
    request_template = '''{"jsonrpc":"2.0","id":"1","method":"%s","params":%s}'''
    args_j = json.dumps(args)

    data_to_send = request_template % (method, args_j)
    headers = {
        'content-type': "application/x-www-form-urlencoded"
    }
    agent = Agent(reactor)
    body = BytesProducer(data_to_send)
    d = agent.request(
        b'POST',
        url,
        Headers({'User-Agent': ['Twisted Web Client Example']}),
        body)

    def cbResponse(response):
        #print('Response received')
        d = readBody(response)
        return d

    d.addCallback(cbResponse)




    #response = requests.request("POST", url, data=data_to_send, headers=headers)
    return d


if __name__ == '__main__':
    print eth_request("eth_getCode", ["0x5901deb2c898d5dbe5923e05e510e95968a35067", "latest"])
