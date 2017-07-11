# -*- coding: utf-8 -*-

from __future__ import print_function
from service import jsonrpc
from config import logger
from utils import eth_utils
from utils import btc_utils
from service import models
from service import db
from utils import error_utils
from bson import json_util
from bson import ObjectId
import json


print(models.get_root_user())

@jsonrpc.method('Zchain.Transaction.History(chainId=str, blockNum=str)')
def index(chainId, blockNum):
    logger.info('Zchain.Transaction.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'STRING')

    trxs = []
    depositTrxs = db.b_deposit_transaction.find({"blockNum": {"$gte": blockNum}}, {"_id": 0})
    withdrawTrxs = db.b_withdraw_transaction.find({"blockNum": {"$gte": blockNum}}, {"_id": 0})
    trxs.append(list(depositTrxs))
    trxs.append(list(withdrawTrxs))

    return {
        'chainId': chainId,
        'data': trxs
    }



@jsonrpc.method('Zchain.Configuration.Set(chainId=str, key=str, value=str)')
def index(chainId, key, value):
    logger.info('Zchain.Configure')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(key) != unicode:
        return error_utils.mismatched_parameter_type('key', 'STRING')
    if type(value) != unicode:
        return error_utils.mismatched_parameter_type('value', 'STRING')
    tbl = db.s_configuration
    data = { "chainId": chainId, "key": key, "value": value }
    result = True
    try:
        tbl.insert_one(data)
    except Exception as e:
        logger.error(str(e))
        result = False
    finally:
        return {
            "result": result
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
        if type(addr) == dict and 'address' in addr:
            addr["chainId"] = chainId
            try:
                addresses.insert_one(addr)
                num += 1
            except Exception as e:
                logger.error(str(e))
        else:
            logger.warn("Invalid chain address: " + str(addr))
    return {
        "valid_num": num
    }


@jsonrpc.method('Zchain.Address.List(chainId=str)')
def index(chainId=str):
    logger.info('Zchain.Address.List')
    addresses = db.b_chain_account
    # chain_accounts = models.BChainAccount.objects()
    # print(chain_accounts)
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    addresses = addresses.find({}, {'_id': 0})
    json_addrs = json_util.dumps(list(addresses))

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
        address = btc_utils.btc_create_address()
        return {'coin':coin,'address':address}



@jsonrpc.method('Zchain.Collection.Amount(coin=String,address=String,amount=Number)')
def zchain_collection_amount(coin,address,amount):
    logger.info('Create_address coin: %s'%(coin))
    if coin == 'eth':
        return {'coin':coin,'result':True}
    elif coin == 'btc':
        return {'coin':coin,'result':True}


@jsonrpc.method('Zchain.CashSweep.History(chainId=str, startTime=str, endTime=str)')
def index(chainId, startTime, endTime):
    """
    查询归账历史
    :param chainId:
    :return:
    """
    logger.info('Zchain.CashSweep.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    trxs = db.b_cash_sweep.find({"chainId": chainId, "sweepDoneTime": {"$ge": startTime}, "sweepDoneTime": {"$lt": endTime}})

    return {
        'chainId': chainId,
        'history': json.loads(json_util.dumps(trxs))
    }


@jsonrpc.method('Zchain.CashSweep.HistoryDetails(cash_sweep_id=String)')
def zchain_query_cash_sweep_details(cash_sweep_id):
    """
    查询某次归账操作记录的具体明细
    :param cash_sweep_id:
    :param offset
    :param limit
    :return:
    """
    logger.info('Zchain.CashSweep.HistoryDetails')
    if type(cash_sweep_id) != unicode:
        return error_utils.mismatched_parameter_type('cash_sweep_id', 'STRING')

    trxs = db.b_cash_sweep.find({'_id': ObjectId(cash_sweep_id)}, {'_id': 0})

    return {
        'cash_sweep_id': cash_sweep_id,
        'total': trxs.count(),
        'result': json.loads(json_util.dumps(trxs))
    }
