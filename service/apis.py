# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger
from utils import eth_utils
from utils import btc_utils
from utils import etp_utils
from service import models
from service import db
from utils import error_utils
from bson import json_util
from bson import ObjectId
import pymongo
import time
import json
from datetime import datetime


@jsonrpc.method('Zchain.Crypt.Sign(chainId=str, addr=str, message=str)')
def zchain_transaction_create(chainId, message):
    logger.info('Zchain.Crypt.Sign')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    signed_message = ""
    if chainId == "btc":
        signed_message = btc_utils.btc_sign_message(addr, message)
    else
        return error_utils.invalid_chainid_type()
    
    return {
        'chainId': chainId,
        'data': signed_message
    }


# @jsonrpc.method('Zchain.Transaction.Create(chainId=str, from_addr=str, to_addr=str, amount=int)')
# def zchain_transaction_create(chainId, from_addr, to_addr, amount):
#     logger.info('Zchain.Transaction.Create')
#     if type(chainId) != unicode:
#         return error_utils.mismatched_parameter_type('chainId', 'STRING')
#     if type(amount) != int:
#         return error_utils.mismatched_parameter_type('trxId', 'INTEGER')

#     if chainId == "btc":
#         eth_utils.eth_create_address()
    
#     return {
#         'chainId': chainId,
#         'data': list(withdrawTrxs)
#     }


@jsonrpc.method('Zchain.Transaction.Withdraw.History(chainId=str, trxId=str)')
def zchain_transaction_withdraw_history(chainId, trxId):
    logger.info('Zchain.Transaction.Withdraw.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(trxId) != unicode:
        return error_utils.mismatched_parameter_type('trxId', 'STRING')

    withdrawTrxs = db.b_withdraw_transaction.find({"TransactionId": trxId, "chainId": chainId}, {"_id": 0})

    return {
        'chainId': chainId,
        'data': list(withdrawTrxs)
    }


@jsonrpc.method('Zchain.Transaction.Deposit.History(chainId=str, blockNum=int)')
def zchain_transaction_deposit_history(chainId, blockNum):
    logger.info('Zchain.Transaction.Deposit.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')

    depositTrxs = db.b_deposit_transaction.find({"chainId": chainId, "blockNum": {"$gte": blockNum}}, {"_id": 0}).sort(
        "blockNum", pymongo.DESCENDING)
    trxs = list(depositTrxs)
    if len(trxs) == 0:
        blockNum = 0
    else:
        blockNum = trxs[0]['blockNum']

    return {
        'chainId': chainId,
        'blockNum': blockNum,
        'data': trxs
    }


@jsonrpc.method('Zchain.Configuration.Set(chainId=str, key=str, value=str)')
def zchain_configuration_set(chainId, key, value):
    logger.info('Zchain.Configure')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(key) != unicode:
        return error_utils.mismatched_parameter_type('key', 'STRING')
    if type(value) != unicode:
        return error_utils.mismatched_parameter_type('value', 'STRING')

    data = {"chainId": chainId, "key": key, "value": value}
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
def zchain_address_setup(chainId, data):
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


@jsonrpc.method('Zchain.Deposit.Address.List(chainId=str)')
def zchain_deposit_address_list(chainId):
    logger.info('Zchain.Address.List')
    addresses = db.b_chain_account
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    addresses = addresses.find({"chainId": chainId}, {'_id': 0, 'address': 1})
    json_addrs = json_util.dumps(list(addresses))

    return {"addresses": json.loads(json_addrs)}


@jsonrpc.method('Zchain.Deposit.Address.Balance(chainId=str, address=str)')
def zchain_deposit_address_balance(chainId, address):
    logger.info('Zchain.Address.Balance')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(address) != unicode:
        return error_utils.mismatched_parameter_type('address', 'STRING')

    address = db.b_chain_account.find_one({"chainId": chainId, "address": address})
    if address is None:
        return error_utils.invalid_deposit_address(address)

    if chainId == "eth":
        balance = eth_utils.eth_get_base_balance(address)
    elif chainId == "btc":
        balance = btc_utils.btc_get_deposit_balance()
        address = "btc_deposit_address"
    elif chainId == "etp":
        balance = etp_utils.etp_get_addr_balance(address)
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        "chainId": chainId,
        "address": address,
        "balance": balance
    }


# TODO, 备份私钥功能暂时注释，正式上线要加回来
@jsonrpc.method('Zchain.Address.Create(chainId=String)')
def zchain_address_create(chainId):
    logger.info('Create_address coin: %s' % (chainId))
    if chainId == 'eth':
        address = eth_utils.eth_create_address()
        print 1
    elif chainId == 'btc':
        address = btc_utils.btc_create_address()
    elif chainId == 'etp' :
        address = etp_utils.etp_create_address()
    else:
        return error_utils.invalid_chainid_type(chainId)
    if address != "":
        if chainId == 'eth':
            pass
            # eth_utils.eth_backup()
        else:
            pass
            # btc_utils.btc_backup_wallet()
        data = db.b_chain_account.find_one({"chainId": chainId, "address": address})
        if data != None:
            return {'chainId': chainId, 'error': '创建地址失败'}
        print 2
        d = {"chainId": chainId, "address": address, "name": "", "pubKey": "", "securedPrivateKey": "",
             "creatorUserId": "", "balance": {}, "memo": "", "createTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        db.b_chain_account.insert(d)
        return {'chainId': chainId, 'address': address}
    else:
        return {'chainId': chainId, 'error': '创建地址失败'}



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
        db.b_config.insert_one({"key": "withdrawaddress", "value": []})
        records = db.b_config.find_one({'key': 'withdrawaddress'}, {'_id': 0})
    for r in records["value"]:
        if r['chainId'] == chainId:
            address = r['address']

    if address == "":
        if chainId == "eth":
            address = eth_utils.eth_create_address()
            # eth_utils.eth_backup()
            records["value"].append({"chainId": "eth", "address": address})
        elif chainId == "btc":
            address = btc_utils.btc_create_withdraw_address()
            btc_utils.btc_backup_wallet()
            records["value"].append({"chainId": "btc", "address": address})
        elif chainId == "etp" :
            address = etp_utils.etp_create_withdraw_address()
            records["value"].append({"chainId": "etp", "address": address})
    db.b_config.update({"key": "withdrawaddress"}, {"$set": {"value": records["value"]}})
    balance = 0.0
    if chainId == "eth":
        balance = eth_utils.eth_get_base_balance(address)
    elif chainId == "btc":
        balance = btc_utils.btc_get_withdraw_balance()
    elif chainId == "etp" :
        balance = etp_utils.etp_get_addr_balance(address)
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'address': address,
        'balance': balance
    }


