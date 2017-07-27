#!/usr/bin/env python
# encoding=utf8

__author__ = 'hasee'

######################################################################
#  数据处理逻辑：
#  1. 先从数据库中获取出上次采集已成功提交的区块号
#  2. 采集前清理掉超出此区块号的tbl_block, tbl_transaction, tbl_transaction_ex, tbl_contract_info表中相关记录
#  3. 考虑到对同一个合约的操作，可能会有并发问题导致的合约操作的先后顺序颠倒的问题，
#       对于tbl_contract_info表，采用replace into ON DUPLICATE的方式
#  4. 对于tbl_contract_abi, tbl_contract_storage, tbl_contract_event表，在遇到注册相关合约相关的交易的处理上，
#       先清理，再插入
######################################################################





import sys
import json
import logging, traceback
from collector_conf import  SYNC_BLOCK_PER_ROUND
from collector_conf import REFRESH_STAT_POST_URL, REFRESH_STAT_POST_DATA
#from utility import to_utf8
#from base import TRX_TYPE_REGISTER_CONTRACT, TRX_TYPE_UPGRADE_CONTRACT, TRX_TYPE_DESTROY_CONTRACT
from base import GlobalVariable
from etp_utils import etp_request
#from httprequest import do_post
#import rpc_biz
import time
from block import BlockInfo,TransactionInfo
from datetime import datetime
import math
import traceback


def do_collect_app(db):

    while True:
        try:
            #程序启动，设置为同步状态
            config = db.b_config
            config.update({"key":"etpsyncstate"},{"key":"etpsyncstate","value": True})


            # 清理上一轮的垃圾数据，包括块数据、交易数据以及合约数据
            GlobalVariable.last_sync_block_num = clear_last_garbage_data(db)
            # 获取当前链上最新块号
            while True:
                GlobalVariable.register_account_dic = {}
                GlobalVariable.upgrade_contract_dic = {}
                latest_block_num = get_latest_block_num(db)
                init_account_info(db)

                print "latest_block_num",latest_block_num
                print "GlobalVariable.last_sync_block_num",GlobalVariable.last_sync_block_num
                if GlobalVariable.last_sync_block_num >= latest_block_num:
                    GlobalVariable.sync_start_per_round = latest_block_num
                    GlobalVariable.sync_end_per_round = latest_block_num
                else:
                    #print 2
                    GlobalVariable.sync_start_per_round = GlobalVariable.last_sync_block_num + 1
                    GlobalVariable.sync_end_per_round = ((
                                                         GlobalVariable.last_sync_block_num + SYNC_BLOCK_PER_ROUND) >= latest_block_num) \
                                                        and latest_block_num or (
                                                        GlobalVariable.last_sync_block_num + SYNC_BLOCK_PER_ROUND)
                print GlobalVariable.sync_start_per_round
                print latest_block_num
                sync_rate = float(GlobalVariable.sync_start_per_round) / latest_block_num
                sync_process = '#' * int(40 * sync_rate) + ' ' * (40 - int(40 * sync_rate))
                sys.stdout.write(
                    "\rsync block [%s][%d/%d], %.3f%%\n" % (sync_process, GlobalVariable.sync_start_per_round,
                                                          latest_block_num, sync_rate * 100))
                while GlobalVariable.sync_start_per_round <GlobalVariable.sync_end_per_round:
                    collect_data_cb(db)
                print 'GlobalVariable.sync_end_per_round',GlobalVariable.sync_end_per_round
                GlobalVariable.last_sync_block_num = GlobalVariable.sync_end_per_round
                config.update({"key": "etpsyncblocknum"}, {"$set":{"key": "etpsyncblocknum", "value": str(GlobalVariable.last_sync_block_num)}})
                if GlobalVariable.sync_start_per_round == latest_block_num:
                    break


            print 'ok'
            time.sleep(10)


        except Exception, ex:
            logging.info(traceback.format_exc())
            print ex
            # 异常情况，60秒后重试eth_utils.py
            time.sleep(60)
            do_collect_app(db)

def init_account_info(db):
    GlobalVariable.db_account_list = []
    GlobalVariable.account_list = []
    GlobalVariable.withdraw_account = []
    GlobalVariable.cash_sweep_account = []


    records = db.b_chain_account.find({"chainId": "etp"})
    for one_account in records:
        GlobalVariable.db_account_list.append(one_account["address"])

    cash_sweep_data = db.b_config.find_one({"key": "cash_sweep_address"})
    if cash_sweep_data is not None:

        for data in cash_sweep_data["value"]:
            if data["chainId"] == "etp":
                GlobalVariable.cash_sweep_account.append(data["address"])
                break

    withdraw_data = db.b_config.find_one({"key": "withdrawaddress"})
    if withdraw_data is not None:
        for data in withdraw_data["value"]:
            if data["chainId"] == "etp":
                GlobalVariable.withdraw_account.append(data["address"])
                break

    ret = etp_request("listaccounts", [])
    json_data = json.loads(ret)
    if json_data.get("accounts") is None:
        raise Exception("get_all_account_list")
    acc_list = json_data.get("accounts")
    for account in acc_list :
        ret = etp_request("listaccounts", [account.get("name"),account.get("name")])
        json_data = json.loads(ret)
        if json_data.get("addresses") is not None :
            addr_list = json_data.get("addresses")
            for addr in addr_list :
                if addr is None :
                    continue
                GlobalVariable.account_list.append(addr)
    GlobalVariable.all_care_account = []
    GlobalVariable.all_care_account.extend(GlobalVariable.account_list)
    GlobalVariable.all_care_account.extend(GlobalVariable.db_account_list)
    GlobalVariable.all_care_account.extend(GlobalVariable.cash_sweep_account)
    GlobalVariable.all_care_account.extend(GlobalVariable.withdraw_account)



def get_all_account_list():
    ret = etp_request("getnewaccount",['hzkai','12345678'])
    print ret
    json_data = json.loads(ret)
    #GlobalVariable.account_list = json_data["result"]


def get_latest_block_num(db):
    ret = etp_request("fetch-height",[])
    safe_block = db.b_config.find_one({"key": "etpsafeblock"})["value"]
    try:
        ret=int(ret)
    except:
        ret=int(safe_block)
    return ret - int(safe_block)



def clear_last_garbage_data(db_pool):

    config = db_pool.b_config
    ret = config.find_one({"key":"etpsyncblocknum"})
    if ret is None:
        config.insert({"key":"etpsyncblocknum","value":"0"})
        last_sync_block_num = int(0)
    else:
        last_sync_block_num = int(ret["value"])
    try:
        db_pool.b_raw_transaction.remove({"blockNum":{"$gte":last_sync_block_num}, "chainId": "etp"})
        db_pool.b_block.remove({"blockNumber":{"$gte":last_sync_block_num}, "chainId": "etp"})

        db_pool.b_raw_transaction_input.remove({"blockNum": {"$gte": last_sync_block_num}, "chainId": "etp"})
        db_pool.b_raw_transaction_output.remove({"blockNum": {"$gte": last_sync_block_num}, "chainId": "etp"})
        db_pool.b_deposit_transaction.remove({"blockNum": {"$gte": last_sync_block_num}, "chainId": "etp"})
        db_pool.b_withdraw_transaction.remove({"blockNum": {"$gte": last_sync_block_num}, "chainId": "etp"})
    except Exception,ex:
        logging.info(traceback.format_exc())
        print ex
    return int(last_sync_block_num)



#采集块数据
def collect_block( db_pool, block_num_fetch):
    # height就是ret,ret 为string
    header_response = etp_request("fetch-header",["-t",block_num_fetch])
    json_header = json.loads(header_response)

    block_info = BlockInfo()
    block_info.from_header_resp(json_header)
    #获取交易信息
    block_response=etp_request("getblock",[block_info.block_id, True])
    json_block = json.loads(block_response)
    block_info.from_trx_resp(json_block.get('txs').get('transactions'))
    block = db_pool.b_block
    txs = json_block.get('txs').get('transactions')
    for tx in txs :
        block_info.trx_count += 1
        if need_to_skip(tx) :
            continue
        tx_data=collect_pretty_transaction(db_pool,block_info,tx)
        update_input_output_tx_data(db_pool,tx,tx_data)
    mongo_data = block.find_one({"blockHash": block_info.block_id})
    # print {"blockHash":block_info.block_id}
    if mongo_data == None:
        block.insert(block_info.get_json_data())
    else:
        block.update({"blockHash": block_info.block_id}, {"$set": block_info.get_json_data()})
    return block_info


def is_contract_trx(receipt_data):
    return False

def is_care_trx(addr):
    temp_list = GlobalVariable.all_care_account
    print temp_list
    if addr in temp_list:
        return True
    return False


def need_to_skip(tx):
    recp={}
    recp['from'] = []
    recp['to'] = []
    for input in tx.get('inputs'):
        if input.get('address') is not None:
            recp['from'].append(input.get('address'))
    for output in tx.get('outputs') :
        if output.get('address') is not None :
            recp['to'].append(output.get('address'))
    for rec in recp['from'] :
        if is_care_trx(rec) :
            return False
    for rec in recp['to'] :
        if is_care_trx(rec) :
            return False
    return True

def update_input_output_tx_data(db_pool,tx,tx_data):
    raw_transaction_input_db = db_pool.b_raw_transaction_input
    raw_transaction_output_db = db_pool.b_raw_transaction_output

    for input in tx.get('inputs'):
        tx_input_data = {}
        tx_input_data["chainID"] = 'etp'
        tx_input_data["TransactionId"] = tx_data['trxid']
        tx_input_data["address"] = input.get('address')
        tx_input_data["blockNum"] = tx_data['blockNum']
        if tx_data.has_key('fromAssets') :
            tx_input_data["assetName"] = tx_data["fromAssets"]
            tx_input_data["amount"] = tx_data['fromAmounts']
        else:
            tx_input_data["assetName"] = "ETP"
            tx_input_data["amount"] = 0
        mongo_data = raw_transaction_input_db.find_one(
            {"TransactionId": tx_data["trxid"], "address": input.get('address'), "chainID": "etp"})
        if mongo_data is None :
            raw_transaction_input_db.insert(tx_input_data)
        else:
            raw_transaction_input_db.update({"TransactionId": tx_data["trxid"],"address":input.get('address'),"chainID":"etp"}, {"$set": tx_input_data})
    for output in tx.get('outputs') :
        tx_output_data = {}
        tx_output_data["chainID"] = 'etp'
        tx_output_data["TransactionId"] = tx_data['trxid']
        tx_output_data["blockNum"] = tx_data['blockNum']
        tx_output_data["address"] = output.get("address")
        if output.get('attachment').get('type') == 'etp' :
            tx_output_data['type'] = 'etp'
            tx_output_data["assetName"] = 'ETP'
            tx_output_data['amount'] = float(output.get('value'))/float(100000000)

        elif output.get('attachment').get('type') == 'asset-transfer':
            tx_output_data['type'] = 'asset-transfer'
            tx_output_data['assetName'] = output.get('attachment').get('symbol')
            tx_output_data['amount'] = float(output.get('attachment').get('quantity'))/float(100000000)
        elif output.get('attachment').get('type') == 'asset-issue':
            tx_output_data['type'] = 'asset-issue'
            tx_output_data['assetName'] = output.get('attachment').get('symbol')
            tx_output_data['quantity'] = float(output.get('attachment').get('quantity'))/float(100000000)
            tx_output_data['decimal_number'] = output.get('attachment').get('decimal_number')
            tx_output_data['issuer'] = output.get('attachment').get('issuer')
            tx_output_data['address'] = output.get('attachment').get('address')
            tx_output_data['description'] = output.get('attachment').get('description')
        mongo_data = raw_transaction_output_db.find_one(
            {"TransactionId": tx_data["trxid"], "address": output.get('address'), "chainID": "etp"})
        if mongo_data is None :
            raw_transaction_output_db.insert(tx_output_data)
        else:
            raw_transaction_output_db.update({"TransactionId": tx_data["trxid"],"address":output.get('address'),"chainID":"etp"}, {"$set": tx_output_data})

def get_amount_from_previous_outputs(hash,addr):
    trx_response = etp_request("fetch-tx",[hash])
    trx = json.loads(trx_response).get("transaction")
    amount={}
    for output in trx.get("outputs"):
        if output.get('address') == addr :
            if output.get('attachment').get('type') == 'etp' :
                if amount.has_key('etp') :
                    amount['etp'] += float(output.get('value'))/float(1000000000)
                else:
                    amount['etp'] = float(output.get('value'))/float(100000000)
            elif output.get('attachment').get('type') == 'asset-transfer':
                if amount.has_key(output.get('attachment').get('symbol')) :
                    amount[output.get('attachment').get('symbol')] += float(output.get('attachment').get('quantity'))/float(100000000)
                else:
                    amount[output.get('attachment').get('symbol')] = float(output.get('attachment').get('quantity'))/float(100000000)
    return amount

def collect_pretty_transaction(db_pool,block,tx):
    raw_transaction_db = db_pool.b_raw_transaction
    b_deposit_transaction = db_pool.b_deposit_transaction
    b_withdraw_transaction = db_pool.b_withdraw_transaction
    trx_data = {}
    trx_data["chainId"] = "etp"
    trx_data["trxid"] = tx.get('hash')
    trx_data["blockid"] = block.block_id
    trx_data["blockNum"] = block.block_num
    trx_data["fromAddresses"] = []
    trx_data['toAssets'] = []
    trx_data["toAddresses"] = []
    trx_data["toAmounts"] = []
    trx_data["fromAssets"] = []
    trx_data["fromAmounts"] = []
    hash = []
    for input in tx.get('inputs') :
        trx_data["fromAddresses"].append(input.get("address"))
        try:
            hash.index([input.get("previous_output").get("hash"),input.get("address")])
            continue
        except:
            hash.append([input.get("previous_output").get("hash"),input.get("address")])
    amount = {}
    for id in hash :
        if id[1] is None :
            continue
        amount = get_amount_from_previous_outputs(id[0],id[1])
        for i in amount :
            trx_data["fromAssets"].append(i)
            trx_data["fromAmounts"].append( str(amount[i]) )
    trx_data['type'] = 'etp'
    for output in tx.get('outputs'):
        addr = output.get("address")
        trx_data["toAddresses"].append(addr)
        trx_data["toAmounts"].append(str(float(output.get("value"))/float(100000000)))
        if output.get('attachment').get('type') == 'etp':
            trx_data['toAssets'].append('ETP')
        elif output.get('attachment').get('type') == 'asset-transfer':
            trx_data['type'] = 'asset-transfer'
            trx_data['toAssets'].append(output.get('attachment').get('symbol'))
            trx_data['toAmounts'].append(str(float(output.get('attachment').get('quantity'))/float(100000000)))
        elif output.get('attachment').get('type') == 'asset-issue':
            trx_data['type'] = 'asset-issue'
            trx_data['symbol'] = output.get('attachment').get('symbol')
            trx_data['quantity'] = float(output.get('attachment').get('quantity'))/float(100000000)
            trx_data['decimal_number'] = output.get('attachment').get('decimal_number')
            trx_data['issuer'] = output.get('attachment').get('issuer')
            trx_data['toAddresses'].append(output.get('attachment').get('address'))
            trx_data['description'] = output.get('attachment').get('description')
    if trx_data['type'] is 'etp' :
        withdraw_data = b_withdraw_transaction.find_one({"chainId": "etp", "TransactionId": trx_data["trxid"]})
        if withdraw_data is None:
            b_withdraw_transaction.insert(
                {"chainId": "etp", "TransactionId": trx_data["trxid"], "fromAddress": trx_data["fromAddresses"],
                "toAddresses": trx_data["toAddresses"],
                "assetName": amount.keys(), "amount": amount.values(), "status": 2, "createTime": block.block_time})
        deposit_data = b_deposit_transaction.find_one({"chainId":"etp","TransactionId":trx_data["trxid"]})
        if deposit_data is None :
            b_deposit_transaction.insert({"chainId": "etp", "TransactionId": trx_data["trxid"], "fromAddress": trx_data["fromAddresses"],
                                       "assetName": trx_data["toAssets"], 'toAddresses':trx_data['toAddresses'],
                                          "amount": trx_data['toAmounts'], "status": 2, "createTime": block.block_time})
            #其他类型
    trx_data["trxFee"] = block.block_bonus - float(3)
    trx_data["FeeAsset"] = "ETP"
    trx_data["isSpecialTransaction"] = False
    trx_data["memo"] = ""
    trx_data["trxTime"] = block.block_time
    trx_data["createtime"] = block.block_time
    trx_data["isDispatched"] = 1
    trx_data["isHandled"] = 1
    block.trx_fee = trx_data["trxFee"]
    mongo_data = raw_transaction_db.find_one({"trxid" : tx.get('hash')})
    if mongo_data == None:
        raw_transaction_db.insert(trx_data)
    else:
        raw_transaction_db.update({"trxid":tx.get('hash')},{"$set":trx_data})
    return trx_data


def update_block_trx_amount(db_pool,block_info):

    block = db_pool.b_block
    block.update({"blockHash":block_info.block_id},{"$set" : {"trxFee":str(block_info.trx_fee)}})

#采集数据
def collect_data_cb(db_pool):
    try:

        while GlobalVariable.sync_start_per_round <= GlobalVariable.sync_end_per_round:
            block_num_fetch = GlobalVariable.sync_start_per_round
            GlobalVariable.sync_start_per_round += 1
            # 采集块
            block_info = collect_block(db_pool, block_num_fetch)
            update_block_trx_amount(db_pool, block_info)

        # 连接使用完毕，需要释放连接
    except Exception, ex:
        traceback.print_exc()
        raise ex



if __name__ == "__main__":
    print get_amount_from_previous_outputs("ac21d53eb0b45d7ca97dd8f2d683c011ebacd8f1282e522ac2cdbcd942c39cd6","MGgtZg2e5qDj7dfXdiBUrXZ7YC8GgMmoMU")