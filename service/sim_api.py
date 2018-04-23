# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger
from utils import eth_utils
from utils import etp_utils
from service import db
from service import sim_btc_plugin,sim_btc_utils_all
from utils import error_utils
import pymongo
from datetime import datetime
import operator


@jsonrpc.method('Zchain.Crypt.Sign(chainId=str, addr=str, message=str)')
def zchain_crypt_sign(chainId, addr, message):
    logger.info('Zchain.Crypt.Sign')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    signed_message = ""
    if sim_btc_plugin.has_key(chainId):
        signed_message = sim_btc_plugin[chainId].sim_btc_sign_message(addr, message)
    else:
        return error_utils.invalid_chainid_type()

    if signed_message == "":
        return error_utils.error_response("Cannot sign message.")

    return {
        'chainId': chainId,
        'data': signed_message
    }


@jsonrpc.method('Zchain.Trans.Sign(chainId=str,addr=str, trx_hex=str, redeemScript=str)')
def zchain_Trans_sign(chainId,addr, trx_hex, redeemScript):
    logger.info('Zchain.Trans.Sign')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    signed_trx = ""
    if sim_btc_plugin.has_key(chainId):
        signed_trx = sim_btc_plugin[chainId].sim_btc_sign_transaction(addr, redeemScript,trx_hex)
    else:
        return error_utils.invalid_chainid_type()

    if signed_trx == "":
        return error_utils.error_response("Cannot sign trans.")

    return {
        'chainId': chainId,
        'data': signed_trx
    }


@jsonrpc.method('Zchain.Trans.broadcastTrx(chainId=str, trx=str)')
def zchain_trans_broadcastTrx(chainId, trx):
    logger.info('Zchain.Trans.broadcastTrx')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_broadcaset_trx(trx)
    else:
        return error_utils.invalid_chainid_type()

    if result == "":
        return error_utils.error_response("Cannot broadcast transactions.")

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Addr.importAddr(chainId=str, addr=str)')
def zchain_addr_importaddr(chainId, addr):
    logger.info('Zchain.Addr.importAddr')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if sim_btc_plugin.has_key(chainId):
        sim_btc_plugin[chainId].btc_import_addr(addr)
    else:
        return error_utils.invalid_chainid_type()
    return {
        'chainId': chainId,
        'data': ""
    }




@jsonrpc.method('Zchain.Trans.createTrx(chainId=str, from_addr=str,dest_info=dict)')
def zchain_trans_createTrx(chainId, from_addr,dest_info):
    logger.info('Zchain.Trans.createTrx')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = {}
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_create_transaction(from_addr,dest_info)
    else:
        return error_utils.invalid_chainid_type()

    if result == {}:
        return error_utils.error_response("Cannot create transaction.")

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Trans.CombineTrx(chainId=str, transactions=list)')
def zchain_trans_CombineTrx(chainId, transactions):
    logger.info('Zchain.Trans.CombineTrx')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_combine_trx(transactions)
    else:
        return error_utils.invalid_chainid_type()

    if result == "":
        return error_utils.error_response("Cannot combine transaction.")

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Trans.DecodeTrx(chainId=str, trx_hex=str)')
def zchain_trans_decodeTrx(chainId, trx_hex):
    logger.info('Zchain.Trans.DecodeTrx')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_decode_hex_transaction(trx_hex)
    else:
        return error_utils.invalid_chainid_type()

    if result == "":
        return error_utils.error_response("Cannot create transaction.")

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Trans.queryTrans(chainId=str, trxid=str)')
def zchain_trans_queryTrx(chainId, trxid):
    logger.info('Zchain.Trans.queryTrans')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_get_transaction(trxid)
    else:
        return error_utils.invalid_chainid_type()

    if result == "":
        return error_utils.error_response("Cannot query transaction.")

    return {
        'chainId': chainId,
        'data': result
    }

@jsonrpc.method('Zchain.Trans.getTrxOuts(chainId=str, addr=str)')
def zchain_trans_getTrxOuts(chainId, addr):
    logger.info('Zchain.Trans.getTrxOuts')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = False
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_query_tx_out(addr)
    else:
        return error_utils.invalid_chainid_type()

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Crypt.VerifyMessage(chainId=str, addr=str, message=str, signature=str)')
def zchain_crypt_verify_message(chainId, addr, message, signature):
    logger.info('Zchain.Crypt.VerifyMessage')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = False
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_verify_signed_message(addr, message, signature)
    else:
        return error_utils.invalid_chainid_type()

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Multisig.Create(chainId=str, addrs=list, amount=int)')
def zchain_multisig_create(chainId, addrs, amount):
    logger.info('Zchain.Multisig.Create')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(addrs) != list:
        return error_utils.mismatched_parameter_type('addrs', 'ARRAY')
    if type(amount) != int:
        return error_utils.mismatched_parameter_type('amount', 'INTEGER')

    address = ""
    redeemScript = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_create_multisig(addrs, amount)
        if result is not None:
            address = result["address"]
            redeemScript = result["redeemScript"]
            mutisig_record = db.get_collection("b_"+chainId+"_multisig_address").find_one({"address": address})
            if mutisig_record is not None:
                db.get_collection("b_"+chainId+"_multisig_address").remove({"address": address})
            data = {"address": address, "redeemScript": redeemScript, "addr_type":0}
            db.get_collection("b_"+chainId+"_multisig_address").insert_one(data)
    else:
        return error_utils.invalid_chainid_type()

    return {
        'chainId': chainId,
        'address': address,
        'redeemScript': redeemScript
    }
@jsonrpc.method('Zchain.Address.validate(chainId=str, addr=str)')
def zchain_address_validate(chainId,addr):
    logger.info("Zchain.Address.validate")
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(addr) != unicode:
        return error_utils.mismatched_parameter_type('addr', 'STRING')
    result = None
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_validate_address(addr)
    else:
        return error_utils.invalid_chainid_type()

    return {
        "chainId":chainId,
        "valid"  : result.get("isvalid")
    }

@jsonrpc.method('Zchain.Multisig.Add(chainId=str, addrs=list, amount=int, addrType=int)')
def zchain_multisig_add(chainId, addrs, amount, addrType):
    logger.info('Zchain.Multisig.Add')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(addrs) != list:
        return error_utils.mismatched_parameter_type('addrs', 'ARRAY')
    if type(amount) != int:
        return error_utils.mismatched_parameter_type('amount', 'INTEGER')
    if type(addrType) != int:
        return error_utils.mismatched_parameter_type('addrType', 'INTEGER')

    address = ""
    if sim_btc_plugin.has_key(chainId):
        multisig_addr = sim_btc_plugin[chainId].sim_btc_add_multisig(addrs, amount)
        if multisig_addr is not None:
            addr_info = sim_btc_plugin[chainId].sim_btc_validate_address(multisig_addr)
            if addr_info is not None:
                multisig_record = db.get_collection("b_"+chainId+"_multisig_address").find_one({"address": multisig_addr})
                if multisig_record is not None:
                    db.get_collection("b_"+chainId+"_multisig_address").remove({"address": multisig_addr})
                data = {"address": addr_info["address"], "redeemScript": addr_info["hex"], "addr_type": addrType}
                db.get_collection("b_"+chainId+"_multisig_address").insert_one(data)
                address = addr_info["address"]
    else:
        return error_utils.invalid_chainid_type()

    return {
        'chainId': chainId,
        'data': address
    }


@jsonrpc.method('Zchain.Transaction.Withdraw.History(chainId=str, account=str, blockNum=int, limit=int)')
def zchain_transaction_withdraw_history(chainId,account ,blockNum, limit):
    logger.info('Zchain.Transaction.Withdraw.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(account) != unicode:
        return error_utils.mismatched_parameter_type('account', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')
    if type(limit) != int:
        return error_utils.mismatched_parameter_type('limit', 'INTEGER')

    withdrawTrxs = db.b_withdraw_transaction.find({"chainId": chainId, "blockNum": {"$gte": blockNum}}, {"_id": 0}).sort(
        "blockNum", pymongo.DESCENDING)
    trxs = list(withdrawTrxs)
    if len(trxs) == 0:
        blockNum = 0
    else:
        blockNum = trxs[0]['blockNum']
    return {
        'chainId': chainId,
        'blockNum': blockNum,
        'data': trxs
    }


@jsonrpc.method('Zchain.Transaction.Deposit.History(chainId=str, account=str, blockNum=int, limit=int)')
def zchain_transaction_deposit_history(chainId,account ,blockNum, limit):
    logger.info('Zchain.Transaction.Deposit.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(account) != unicode:
        return error_utils.mismatched_parameter_type('account', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')
    if type(limit) != int:
        return error_utils.mismatched_parameter_type('limit', 'INTEGER')

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


# TODO, 备份私钥功能暂时注释，正式上线要加回�?
@jsonrpc.method('Zchain.Address.Create(chainId=String)')
def zchain_address_create(chainId):
    logger.info('Create_address coin: %s' % (chainId))
    if chainId == 'eth':
        address = eth_utils.eth_create_address()
    elif sim_btc_plugin.has_key(chainId):
        address = sim_btc_plugin[chainId].sim_btc_create_address()
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
        d = {"chainId": chainId, "address": address, "name": "", "pubKey": "", "securedPrivateKey": "",
             "creatorUserId": "", "balance": {}, "memo": "", "createTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        db.b_chain_account.insert(d)
        return {'chainId': chainId, 'address': address}
    else:
        return {'chainId': chainId, 'error': '创建地址失败'}


@jsonrpc.method('Zchain.Query.QueryTransactionHistory(chainId=str,address=str,startIndex=int,pageSize=int)')
def zchain_query_querytransaction(chainId,address,startIndex,pageSize):
    logger.info('Zchain.Query.QueryTransactionHistory')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if not chainId.lower() in sim_btc_utils_all:
        return {'chainId':chainId,'result':"[]",'have_next':0,'count':0}
    data = db.b_address_trx.find_one({"chainId":chainId,"address":address},{"_id":0,"chainId":0})
    if data is None:
        return {'chainId':chainId,'result':"[]",'have_next':0,'count':0}
    # sort result data by block_num and trx_index
    list_data = data["trxdata"]
    list_data.sort(key=operator.itemgetter("block_num", "trx_index"))
    temp_list_data = []
    for data in list_data:
        if temp_list_data.count(data) == 0:
            temp_list_data.append(data)
    list_data = temp_list_data
    result_need_data = list_data[pageSize * startIndex:pageSize * startIndex+pageSize]
    count = len(list_data)
    have_next = 0 if count <= pageSize*(startIndex+1) else 1
    result_data = []
    for one_data in result_need_data:
        one_trx_data = db.b_cache_transaction.find_one({"chainId":chainId,"txid":one_data["trxid"]},{"_id":0})
        if one_trx_data is None:

            one_trx_data = sim_btc_plugin[chainId.lower()].sim_btc_query_transacation(one_data["trxid"])
            one_trx_data["chainId"] = chainId
            db.b_cache_transaction.insert(one_trx_data)
            one_trx_data.pop("_id")


        result_data.append(one_trx_data)

    return {'chainId': chainId, 'result': result_data, 'have_next': have_next, 'count': count}


def listP(list_old):
    list_new = []
    dict_new = {}
    dict_new = dict.fromkeys(list_old,1)  #调用dict内嵌函数生成新的dict对象
    #将dict的key值直接转成list
    list_new = list(dict_new.keys())
    return list_new


@jsonrpc.method('Zchain.Query.QueryBalance(chainId=str,address=str)')
def zchain_query_querybalance(chainId,address):
    logger.info('Zchain.Query.QueryBalance')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    chainId = chainId.upper()
    if not chainId.lower() in sim_btc_utils_all:
        return {'chainId':chainId,'error':"sim not init"}
    data = db.b_address_trx.find_one({"chainId":chainId,"address":address},{"_id":0,"chainId":0})
    if data is None:
        return {'chainId':chainId,'result':"address not exists",'have_next':0,'count':0}
    # sort result data by block_num and trx_index
    list_data = data["trxdata"]
    list_data.sort(key=operator.itemgetter("block_num", "trx_index"))
    temp_list_data = []
    for data in list_data:
        if temp_list_data.count(data)==0:
            temp_list_data.append(data)
    list_data = temp_list_data
    count = len(list_data)
    result_data = []
    mongo_trx_count = 0
    mongo_balance_data = db.b_cache_balance.find_one({"chainId":chainId,"address":address},{"_id":0})
    if mongo_balance_data is not None:
        mongo_trx_count = mongo_balance_data["trxcount"]

    if mongo_trx_count == count:
        return {'chainId': chainId, "address": address, 'result': mongo_balance_data["balance"]}

    for one_data in list_data:
        one_trx_data = db.b_cache_transaction.find_one({"chainId":chainId,"txid":one_data["trxid"]},{"_id":0})
        if one_trx_data is None:

            one_trx_data = sim_btc_plugin[chainId.lower()].sim_btc_query_transacation(one_data["trxid"])
            one_trx_data["chainId"] = chainId
            db.b_cache_transaction.insert(one_trx_data)
            one_trx_data.pop("_id")

        result_data.append(one_trx_data)
    balance = 0
    for data in result_data:
        print data["txid"]
        for vin in data["vin"]:
            #print "vin:",vin
            if vin["address"][0] == address:
                balance -= vin["value"]
        for vout in data["vout"]:

            if vout["address"][0] == address:
                print "vout:", vout
                balance += vout["value"]

    balance =round(balance,8)

    if mongo_balance_data is None:
        db.b_cache_balance.insert({"chainId":chainId,"address":address,"trxcount":count,"balance":balance})
    else:
        db.b_cache_balance.update({"chainId": chainId, "address": address},{"$set":{"trxcount": count, "balance": balance} })


    return {'chainId': chainId,"address":address, 'result': balance}


@jsonrpc.method('Zchain.Withdraw.GetInfo(chainId=str)')
def zchain_withdraw_getinfo(chainId):
    """
    查询提现账户的信�?
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
        elif sim_btc_plugin.has_key(chainId):
            address = sim_btc_plugin[chainId].sim_btc_create_withdraw_address()
            sim_btc_plugin.sim_btc_backup_wallet()
            records["value"].append({"chainId": chainId, "address": address})
        elif chainId == "etp":
            address = etp_utils.etp_create_withdraw_address()
            records["value"].append({"chainId": "etp", "address": address})
    db.b_config.update({"key": "withdrawaddress"}, {"$set": {"value": records["value"]}})
    balance = 0.0
    if chainId == "eth":
        balance = eth_utils.eth_get_base_balance(address)
    elif sim_btc_plugin.has_key(chainId):
        balance = sim_btc_plugin.sim_btc_get_withdraw_balance()
    elif chainId == "etp":
        balance = etp_utils.etp_get_addr_balance(address)
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'address': address,
        'balance': balance
    }


