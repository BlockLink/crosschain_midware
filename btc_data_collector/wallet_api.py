# -*- coding: utf-8 -*-
import requests
import json
from base64 import encodestring
from twisted.internet import reactor
from twisted.web.http_headers import Headers
from twisted.web.client import Agent, readBody
from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implementer
import twisted.web.client

from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer
from collector_conf import BTCCollectorConfig

@implementer(IBodyProducer)
class BytesProducer(object):
    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class WalletApi:
    def __init__(self, name, conf):
        self.name = name
        self.config = conf

    @inlineCallbacks
    def http_request(self, method, args):
        url = "http://%s:%s" % (self.config["host"], self.config["port"])
        user = 'a'
        passwd = 'b'
        basestr = encodestring('%s:%s' % (user, passwd))[:-1]
        args_j = json.dumps(args)
        payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
        headers = {
            'User-Agent': ['Twisted Web Client Example'],
            'content-type': ["text/plain"],
            'authorization': ["Basic %s" % (basestr)],
            'cache-control': ["no-cache"]
        }

        agent = twisted.web.client.Agent(reactor)
        body = BytesProducer(payload)
        d = agent.request(
            b'POST',
            url,
            Headers(headers),
            body)

        def cbResponse(response):
            # print('Response received')
            d = readBody(response)
            return d

        def cbErrRespones(failure):
            print str(failure)

        d.addCallback(cbResponse)
        d.addErrback(cbErrRespones)
        res = yield d
        try:
            json_data = json.loads(res)
        except :
            print "json retry:",res
            json_data = yield self.http_request(method,args)
        #response = requests.request("POST", url, data=payload, headers=headers)
        #rep = response.json()
        #return rep
        returnValue(json_data)

PER_BLOCK_COUNT = 5000
trx_count =0


import time
from twisted.internet.defer import DeferredList, inlineCallbacks, returnValue,Deferred

@inlineCallbacks
def get_block(db_pool,wallet_api,start_num):
    global  trx_count
    try:
        for j in range(PER_BLOCK_COUNT):
            data = yield wallet_api.http_request("getblockhash",[start_num+j])
            data = yield wallet_api.http_request("getblock", [data["result"],2])
            #print data
            #print start_num+j
            trx_count += len(data["result"]["tx"])
            #for tx in data["result"]["tx"]:
            #    trx_count +=len(tx["vin"])
            '''for vout in tx["vout"]:
                    if vout.has_key("scriptPubKey"):
                        if vout["scriptPubKey"].has_key("addresses"):
                            yield db_pool.b_address_trx.find_one({"chainId":"BTC","address":vout["scriptPubKey"]["addresses"][0]},{"chainId":1,"address":1})
                '''
            '''for tx in data["result"]["tx"]:
                for vout in tx["vout"]:
                    #multisig
                    if vout["scriptPubKey"].has_key("addresses"):
                        if len(vout["scriptPubKey"]["addresses"])>1 and vout["scriptPubKey"]["type"]!="multisig":
                            print tx'''
            #print data
    except Exception,ex:
        print ex


@inlineCallbacks
def http_test(db):
    try:
        #multisig_address_cache = yield db.b_btc_multisig_address.find({},{"address":1,"addr_type":1})
        #print multisig_address_cache
        conf = {"host": "192.168.1.123", "port": 10888}
        wallet_api = WalletApi("btc", conf)
        global  trx_count
        temp_time =time.time()
        defer_list = []
        for i in range(20):
            d = get_block(db,wallet_api, 0+i * PER_BLOCK_COUNT)
            defer_list.append(d)
        yield DeferredList(defer_list)
        print trx_count
        time_cost = time.time() - temp_time
        print "cost time:",time_cost
        print "trx per sec: ",trx_count/time_cost
        #new_time = time.time()
        #defer_list1 = []
        #for i in range(20):
        #    d = get_block(wallet_api,476000+ i * PER_BLOCK_COUNT)
        #    defer_list1.append(d)
        #yield DeferredList(defer_list1)
        #print "new cost time:", time.time() - new_time
    except Exception,ex:
        print ex

import txmongo
from collector_conf import CollectorConfig

if __name__ == '__main__':
    config = CollectorConfig()
    client = txmongo.MongoConnectionPool(host=config.MONGO_HOST, port=config.MONGO_PORT, pool_size=config.DB_POOL_SIZE)
    # client = MongoClient(host=config.MONGO_HOST, port=config.MONGO_PORT)
    client[config.MONGO_NAME].authenticate(config.MONGO_USER, config.MONGO_PASS)
    db = client[config.MONGO_NAME]

    reactor.callWhenRunning(http_test,db)
    reactor.run()