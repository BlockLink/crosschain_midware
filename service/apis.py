# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger

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


@jsonrpc.method('Zchain.Address.List')
def index():
    logger.info('Zchain.Address.List')
    return {
        "addresses": [
            "124",
            "234"
        ]
    }




@jsonrpc.method('Zchain.Create.Address(coin=String)')
def zchain_create_address(coin):
    logger.info('Create_address coin: %s'%(coin))
    if coin == 'eth':
        address = ''
        return {'coin':coin,'address':address}
    elif coin == 'btc':
        address = ''
        return {'coin':coin,'address':address}



@jsonrpc.method('Zchain.Collection.Amount(coin=String,address=String,amount=double)')
def zchain_collection_amount(coin,address,amount):
    logger.info('Create_address coin: %s'%(coin))
    if coin == 'eth':
        return {'coin':coin,'result':True}
    elif coin == 'btc':
        return {'coin':coin,'result':True}


