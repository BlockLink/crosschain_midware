# -*- coding: utf-8 -*-

from __future__ import print_function
from service import jsonrpc
from config import logger
from utils import eth_utils
from service import models
from service import db
from utils import error_utils
from bson import json_util as jsonb
import json

print(models.get_root_user())

@jsonrpc.method('Zchain.Transaction.History(chainId=str, blockNum=str)')
def index(chainId, blockNum):
    logger.info('Zchain.Transaction.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'STRING')

    depositTrxs = db.b_deposit_transaction.find({"blockNum": {"$ge": blockNum}}, {"_id": 0})
    withdrawTrxs = db.b_withdraw_transaction.find({"blockNum": {"$ge": blockNum}}, {"_id": 0})
    depositTrxs.extend(withdrawTrxs)

    return {
        'data': jsonb.loads(jsonb.dumps(list(depositTrxs)))
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


@jsonrpc.method('Zchain.CashSweep.History(chainId=str, startTime=str, endTime=str)')
def index(chainId, startTime, endTime):
    logger.info('Zchain.CashSweep.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    trxs = db.b_cash_sweep.find({"sweepDoneTime": {"$ge": startTime}, "sweepDoneTime": {"$lt": endTime}}, {'_id': 0})

    return {
        'data': jsonb.loads(jsonb.dumps(list(trxs)))
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
    json_addrs = jsonb.dumps(list(addresses))

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


@jsonrpc.method('Zchain.CashSweep.QueryHistory(chainId=String)')
def zchain_query_cash_sweep_history(chainId):
  """
  查询归账历史
  :param chainId:
  :return:
  """
  logger.info("query cash sweep history of chain %s" % chainId)
  return {
    'chainId': chainId,
    'history': [
    ],
  }

@jsonrpc.method('Zchain.CashSweep.QueryHistoryDetails(cash_sweep_id=String,offset=int,limit=int)')
def zchain_query_cash_sweep_details(cash_sweep_id, offset, limit):
  """
  查询某次归账操作记录的具体明细
  :param cash_sweep_id:
  :param offset
  :param limit
  :return:
  """
  return {
    'cash_sweep_id': cash_sweep_id,
    'total': 0,
    'result': [
      # TODO:每一项是一条归账操作计划的一条需要转账的记录
    ],
  }
