# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger
from utils import eth_utils
from service import db
from utils import error_utils
from bson import json_util as jsonb
import json

@jsonrpc.method('Zchain.Transaction.History')
def index():
    logger.info('Zchain.Transaction.History')
    return {
        'last_block_num': 0,
        'from_block_num': 0,
        'transactions': [
            'test'
        ]
    }



@jsonrpc.method('Zchain.Configure')
def index():
    logger.info('Zchain.Configure')
    return {
        "result": True
    }


@jsonrpc.method('Zchain.CashSweep.History')
def index():
    logger.info('Zchain.CashSweep.History')
    return {
        "history": [
            {
                "date_time": "2011-1-1 00:00:00",
                "transactions": [
                    {
                        "from_address": "123",
                        "to_address": "234",
                        "amount": 1
                    }
                ]
            }
        ]
    }


@jsonrpc.method('Zchain.Address.Setup(chainId=str, data=list)')
def index(chainId, data):
    logger.info('Zchain.Address.Setup')
    addresses = db.b_chain_account
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(data) != list:
        return error_utils.mismatched_parameter_type('data', 'ARRAY')

    num = 0
    for addr in data:
        if type(addr) == dict and addr.has_key('address'):
            addr["chainId"] = chainId
            try:
                addresses.insert_one(addr)
                num += 1
            except Exception, e:
                logger.error(str(e))
        else:
            logger.warn("Invalid chain address: " + str(addr))
    return {
        "valid_num": num
    }


@jsonrpc.method('Zchain.Address.List(chainId=str)')
def index(chainId=str):
    logger.info('Zchain.Address.List')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    addresses = db.b_chain_account.find({}, {"_id": 0})
    json_addrs = jsonb.dumps(list(addresses))

    #return json.loads(json_addrs)
    return { "addresses": json.loads(json_addrs) }




@jsonrpc.method('Zchain.Create.Address(coin=String)')
def zchain_create_address(coin):
    logger.info('Create_address coin: %s'%(coin))
    if coin == 'eth':
        address = eth_utils.eth_create_address()
        if address !=  "":
            return {'coin':coin,'address':address}
        else:
            return {'coin':coin,'error':'创建地址失败'}
    elif coin == 'btc':
        address = ''
        return {'coin':coin,'address':address}



@jsonrpc.method('Zchain.Collection.Amount(coin=String,address=String,amount=Number)')
def zchain_collection_amount(coin,address,amount):
    logger.info('Create_address coin: %s'%(coin))
    if coin == 'eth':
        return {'coin':coin,'result':True}
    elif coin == 'btc':
        return {'coin':coin,'result':True}


