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
    url = "http://%s:%s" % (ETH_URL, ETH_PORT)
    request_template = '''{"jsonrpc":"2.0","id":"1","method":"%s","params":%s}'''
    args_j = json.dumps(args)

    data_to_send = request_template % (method, args_j)
    headers = {
        'Content-Type': "application/json"
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
def eth_request_from_db(method,args):
    try:
        url = "http://%s:%s" % (ETH_URL, ETH_PORT)
        request_template = '''{"id":"1","method":"%s","params":%s}'''
        args_j = json.dumps(args)

        data_to_send = request_template % (method, args_j)
        #print data_to_send
        agent = Agent(reactor)
        body = BytesProducer(data_to_send)
        d = agent.request(
            b'POST',
            url,
            Headers({'Content-Type': ['application/json']}),
            body)

        def cbResponse(response):
            # print('Response received')
            d = readBody(response)
            return d

        d.addCallback(cbResponse)
    #response = requests.request("POST", url, data=data_to_send, headers=headers)
        return d
    except Exception,ex:
        print ex


if __name__ == '__main__':
    print eth_request_from_db("Service.GetNormalHistory", [50])
