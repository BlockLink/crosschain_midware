# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger
from utils import eth_utils
from utils import btc_utils
from service import models
from service import db
from utils import error_utils
from bson import json_util
from bson import ObjectId
import time
import json


print(models.get_root_user())

@jsonrpc.method('Zchain.Transaction.History(chainId=str, blockNum=int)')
def index(chainId, blockNum):
    logger.info('Zchain.Transaction.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')

    trxs = []
    depositTrxs = db.b_deposit_transaction.find({"chainId": chainId, "blockNum": {"$gte": blockNum}}, {"_id": 0})
    withdrawTrxs = db.b_withdraw_transaction.find({"chainId": chainId, "blockNum": {"$gte": blockNum}}, {"_id": 0})
    trxs.extend(list(depositTrxs))
    trxs.extend(list(withdrawTrxs))

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

    data = { "chainId": chainId, "key": key, "value": value }
    result = True
    try:
        db.b_config.insert_one(data)
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




@jsonrpc.method('Zchain.Address.Create(chainId=String)')
def zchain_address_create(chainId):
    logger.info('Create_address coin: %s'%(chainId))
    address = ""
    if chainId == 'eth':
        address = eth_utils.eth_create_address()
    elif chainId == 'btc':
        address = btc_utils.btc_create_address()
    else:
        return error_utils.invalid_chaind_type(chainId)
    if address != "":
        data = db.b_chain_account.find_one({"chainId":chainId,"address":address})
        if data != None:
            return {'coin':chainId,'error':'创建地址失败'}
        d = {"chainId":chainId,"address":address,"name":"","pubKey":"","securedPrivateKey":"","creatorUserId":"","balance":{},"memo":"","createTime":time.time()}
        db.b_chain_account.insert(d)
        return {'coin':chainId,'address':address}
    else:
        return {'coin':chainId,'error':'创建地址失败'}


#TODO, 要返回opId
@jsonrpc.method('Zchain.CashSweep(chainId=String)')
def zchain_collection_amount(chainId):
    logger.info('CashSweep chainId: %s'%(chainId))
    addressList = []
    chain_account = db.b_chain_account
    resultData = chain_account.find({"chainId":chainId})
    for one_data in resultData:
        addressList.append(one_data["address"])
    cash_sweep_data = db.b_config.find_one({"key":"cash_sweep_address"})
    if cash_sweep_data is None:
        return error_utils.mis_cash_sweep_config()
    for data in cash_sweep_data["value"]:
        if data["chainId"] == chainId:
            cash_sweep_account = data["address"]
            break
    if chainId == 'eth':
        resp,err = eth_utils.eth_collect_money(cash_sweep_account,addressList)
        if resp is None:
            return error_utils.unexcept_error(err)


    elif chainId == 'btc':
        try:
            trx_id = btc_utils.btc_collect_money()
            if trx_id == "":
                return {'coin':chainId,'result':False}
            else:
                return {'coin':chainId,'result':True}
        except Exception as e:
            return {'coin':chainId,'result':False}
    else:
        return error_utils.invalid_chaind_type(chainId)
    for one_data in resp["data"]:
        one_data[""]
        pass
    for one_data in resp["errdata"]:
        pass
    return {'chainId': chainId, 'result': True}



#TODO, 实现与接口不符
@jsonrpc.method('Zchain.CashSweep.History(chainId=str, opId=str, startTime=str, endTime=str)')
def index(chainId, opId, startTime, endTime):
    """
    查询归账历史
    :param chainId:
    :return:
    """
    logger.info('Zchain.CashSweep.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(opId) != unicode:
        return error_utils.mismatched_parameter_type('opId', 'STRING')

    if opId == "":
        trxs = db.b_cash_sweep.find(
            {"chainId": chainId, "sweepDoneTime": {"$ge": startTime}, "sweepDoneTime": {"$lt": endTime}})
    else:
        trxs = db.b_cash_sweep.find(
            {"chainId": chainId, "opId": opId, "sweepDoneTime": {"$ge": startTime}, "sweepDoneTime": {"$lt": endTime}})

    return {
        'chainId': chainId,
        'history': json.loads(json_util.dumps(trxs))
    }


#TODO, 可能不需要了，需要确认
@jsonrpc.method('Zchain.CashSweep.HistoryDetails(cash_sweep_id=String)')
def zchain_query_cash_sweep_details(cash_sweep_id):
    """
    查询某次归账操作记录的具体明细
    :param cash_sweep_id:
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



@jsonrpc.method('Zchain.Withdraw.GetInfo(chainId=str)')
def zchain_withdraw_getinfo(chainId):
    """
    查询提现账户的信息
    :param chainId:
    :return:
    """
    logger.info('Zchain.Withdraw.GetInfo')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    records = db.b_config.find_one({'key': 'withdrawaddress'}, {'_id': 0})
    address = ""
    if records == None:
         db.b_config.insert_one({"key":"withdrawaddress","value":[]})
         records = db.b_config.find_one({'key': 'withdrawaddress'}, {'_id': 0})
    for r in records["value"]:
        if r['chainId'] == chainId:
            address = r['address']

    if address == "":
        if chainId == "eth":
            address = eth_utils.eth_create_address()
            records["value"].append({"chainId":"eth","address":address})
        elif chainId == "btc":
            address = btc_utils.btc_create_withdraw_address()
            records["value"].append({"chainId":"btc","address":address})
    db.b_config.update({"key":"withdrawaddress"},{"$set":{"value":records["value"]}})
    balance = 0.0
    if chainId == "eth":
        balance = eth_utils.eth_get_base_balance(address)
    elif chainId == "btc":
        balance = btc_utils.btc_get_withdraw_balance()
    else:
        return error_utils.invalid_chaind_type(chainId)

    return {
        'chainId': chainId,
        'address': address,
        'balance': balance
    }


#TODO, 待实现
@jsonrpc.method('Zchain.Withdraw.Execute(chainId=str, address=str, amount=Number)')
def zchain_withdraw_execute(chainId, address, amount):
    """
    执行提现操作
    :param chainId:
    :return:
    """
    logger.info('Zchain.Withdraw.Execute')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(address) != unicode:
        return error_utils.mismatched_parameter_type('address', 'STRING')
    if type(amount) != float and type(amount) != int:
        return error_utils.mismatched_parameter_type('amount', 'FLOAT/INTEGER')

    return {
        'amount': 1.03,
        'fee': 0.01,
        'trxId': "0xa31dcef"
    }
