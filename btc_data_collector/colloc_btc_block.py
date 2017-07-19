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





import logging
import sys
import traceback

from collector_conf import  SYNC_BLOCK_PER_ROUND
#from utility import to_utf8
#from base import TRX_TYPE_REGISTER_CONTRACT, TRX_TYPE_UPGRADE_CONTRACT, TRX_TYPE_DESTROY_CONTRACT
from base import GlobalVariable_btc
from btc_utils import btc_request
#from httprequest import do_post
#import rpc_biz
import time
from block_btc import BlockInfoBtc
from datetime import datetime


def do_collect_app(db):

    while True:
        try:
            #程序启动，设置为同步状态
            config = db.b_config
            config.update({"key":"btcsyncstate"},{"key":"btcsyncstate","value":"true"})


            # 清理上一轮的垃圾数据，包括块数据、交易数据以及合约数据
            GlobalVariable_btc.last_sync_block_num = clear_last_garbage_data(db)

            # 获取当前链上最新块号
            while True:
                GlobalVariable_btc.register_account_dic = {}
                GlobalVariable_btc.upgrade_contract_dic = {}
                latest_block_num = get_latest_block_num(db)
                print "latest_block_num",latest_block_num
                print "GlobalVariable_btc.last_sync_block_num",GlobalVariable_btc.last_sync_block_num
                if GlobalVariable_btc.last_sync_block_num >= latest_block_num:
                    GlobalVariable_btc.sync_start_per_round = latest_block_num
                    GlobalVariable_btc.sync_end_per_round = latest_block_num
                else:
                    GlobalVariable_btc.sync_start_per_round = GlobalVariable_btc.last_sync_block_num + 1
                    GlobalVariable_btc.sync_end_per_round = ((
                                                         GlobalVariable_btc.last_sync_block_num + SYNC_BLOCK_PER_ROUND) >= latest_block_num) \
                                                        and latest_block_num or (
                                                        GlobalVariable_btc.last_sync_block_num + SYNC_BLOCK_PER_ROUND)
                print GlobalVariable_btc.sync_start_per_round
                print latest_block_num
                sync_rate = float(GlobalVariable_btc.sync_start_per_round) / latest_block_num
                sync_process = '#' * int(40 * sync_rate) + ' ' * (40 - int(40 * sync_rate))
                sys.stdout.write(
                    "\rsync block [%s][%d/%d], %.3f%%\n" % (sync_process, GlobalVariable_btc.sync_start_per_round,
                                                          latest_block_num, sync_rate * 100))
                while GlobalVariable_btc.sync_start_per_round <GlobalVariable_btc.sync_end_per_round:
                    collect_data_cb(db)
                GlobalVariable_btc.last_sync_block_num = GlobalVariable_btc.sync_end_per_round
                config.update({"key": "btcsyncblocknum"}, {"$set":{"key": "btcsyncblocknum", "value": str(GlobalVariable_btc.last_sync_block_num)}})
                if GlobalVariable_btc.sync_start_per_round == latest_block_num:
                    break


            print 'ok'
            time.sleep(10)


        except Exception, ex:
            logging.info(traceback.format_exc())
            print ex
            # 异常情况，60秒后重试eth_utils.py
            time.sleep(60)
            do_collect_app(db)


def get_latest_block_num(db):
    ret = btc_request("getblockcount",[])
    real_block_num = ret['result']
    safe_block = db.b_config.find_one({"key":"btcsafeblock"})["value"]
    return int(real_block_num) - int(safe_block)



def clear_last_garbage_data(db_pool):

    config = db_pool.b_config
    ret = config.find_one({"key":"btcsyncblocknum"})
    last_sync_block_num = int(ret["value"])
    try:
        db_pool.b_raw_transaction.remove({"blockNum":{"$gte":last_sync_block_num},"chainId":"btc"})
        db_pool.b_block.remove({"blockNumber":{"$gte":last_sync_block_num},"chainId":"btc"})

        db_pool.b_raw_transaction_input.remove({"blockNum": {"$gte": last_sync_block_num},"chainId":"btc"})
        db_pool.b_raw_transaction_output.remove({"blockNum": {"$gte": last_sync_block_num},"chainId":"btc"})
        db_pool.b_deposit_transaction.remove({"blockNum": {"$gte": last_sync_block_num},"chainId":"btc"})
        db_pool.b_withdraw_transaction.remove({"blockNum": {"$gte": last_sync_block_num},"chainId":"btc"})
    except Exception,ex:
        print ex
    return int(last_sync_block_num)



#采集块数据
def collect_block( db_pool, block_num_fetch):
    ret1 = btc_request("getblockhash",[block_num_fetch])
    if ret1['result'] == None:
        raise Exception("blockchain_get_block error")
    block_hash = ret1['result']
    ret2 = btc_request("getblock",[str(block_hash)])
    if ret2['result'] == None:
        raise Exception("blockchain_get_block error")
    json_data = ret2['result']
    if len(json_data["tx"]) > 0:
        print "has transactions:", block_num_fetch
    block_info = BlockInfoBtc()
    block_info.from_block_resp(json_data)
    block = db_pool.b_block
    mongo_data = block.find_one({"blockHash":block_info.block_id})

    if mongo_data == None:
        block.insert(block_info.get_json_data())
    else:
        block.update({"blockHash":block_info.block_id},{"$set":block_info.get_json_data()})

    return block_info


def get_transaction_data(trx_id):

    ret = btc_request("gettransaction",[trx_id])
    if ret["result"] is None:
        resp_data = None
    else:
        resp_data = ret["result"]
    return resp_data



def collect_pretty_transaction(db_pool, base_trx_data,block_num):
    #处理交易
    raw_transaction_db = db_pool.b_raw_transaction
    trx_data = {}
    amount = 0.0
    from_address = ""
    to_address = ""
    from_account = ""
    to_account = ""
    trx_data["chainId"] = "btc"
    trx_data["trxid"] = base_trx_data["txid"]
    trx_data["blockid"] = base_trx_data["blockhash"]
    trx_data["blockNum"] = block_num
    trxs = base_trx_data["details"]
    trx_data["toAmounts"] = []
    trx_data["fromAmounts"] = []
    trx_data["trxFee"] = []
    trx_data["fromAddresses"] = []
    trx_data["toAddresses"] = []
    for trx in trxs:
        if trx["category"] == "send":
            from_address = trx["address"]
            from_account = trx["account"]
            trx_data["fromAddresses"].append(trx["address"])
            trx_data["fromAmounts"].append(trx["amount"])
            trx_data["fromAssets"] = "btc"
            trx_data["trxFee"].append(trx['fee'])
            trx_data["FeeAsset"] = "btc"
        elif trx["category"] == "receive":
            to_address = trx["address"]
            to_account = trx["account"]
            trx_data["toAddresses"].append(trx["address"])
            amount += trx["amount"]
            trx_data["toAmounts"].append(trx["amount"])
            trx_data["toAssets"] = "btc"
    trx_data["trxTime"] = datetime.utcfromtimestamp(base_trx_data['time']).strftime("%Y-%m-%d %H:%M:%S")
    trx_data["createtime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trx_data["isDispatched"] = 0
    trx_data["isHandled"] = 0
    mongo_data = raw_transaction_db.find_one({"trxid" : base_trx_data["txid"]})
    if mongo_data == None:
        raw_transaction_db.insert(trx_data)
    else:
        raw_transaction_db.update({"trxid":base_trx_data["txid"]},{"$set":trx_data})
    raw_transaction_input_db = db_pool.b_raw_transaction_input
    raw_transaction_output_db = db_pool.b_raw_transaction_output
    for trx in trxs:
        if trx["category"] == "send":
            trx_input_data = {}
            trx_input_data["chainID"] = "btc"
            trx_input_data["TransactionId"] = trx_data["trxid"]
            trx_input_data["address"] = trx["address"]
            trx_input_data["blockNum"] = trx_data["blockNum"]
            trx_input_data["assetName"] = "btc"
            trx_input_data["amount"] = str(trx["amount"])
            mongo_data = raw_transaction_input_db.find_one({"TransactionId": base_trx_data["txid"],"address":trx["address"],"chainID":"btc"})
            if mongo_data == None:
                raw_transaction_input_db.insert(trx_input_data)
            else:
                raw_transaction_input_db.update({"trxid": base_trx_data["txid"],"address":trx["address"],"chainID":"btc"}, {"$set": trx_data})
        elif trx["category"] == "receive":
            trx_output_data = {}
            trx_output_data["chainID"] = "btc"
            trx_output_data["TransactionId"] = trx_data["trxid"]
            trx_output_data["blockNum"] = trx_data["blockNum"]
            trx_output_data["address"] = trx["address"]
            trx_output_data["assetName"] = "btc"
            trx_output_data["amount"] = str(trx["amount"])
            mongo_data = raw_transaction_output_db.find_one({"TransactionId": base_trx_data["txid"], "address":trx["address"],"chainID":"btc"})
            if mongo_data == None:
                raw_transaction_output_db.insert(trx_output_data)
            else:
                raw_transaction_output_db.update({"TransactionId": base_trx_data["txid"], "address":trx["address"],"chainID":"btc"},
                                          {"$set": trx_data})

    if from_account == "btc_test":
        print "handle address from"
        #b_cash_sweep  b_cash_sweep_plan_detail
        cash_detail_data = db_pool.b_cash_sweep_plan_detail.find_one({"chainId":"btc","trxId":trx_data["trxid"]})
        if cash_detail_data == None:
            db_pool.b_cash_sweep_plan_detail.insert({"chainId":"btc","trxId":trx_data["trxid"],"fromAddress":from_address,"sweepAddress":to_address,"successCoinAmount":amount,"status":1,"createTime":trx_data["createtime"]})
        else:
            db_pool.b_cash_sweep_plan_detail.update({"chainId":"btc","trxId":trx_data["trxid"]},{"$set":{"fromAddress":from_address,"sweepAddress":to_address,"successCoinAmount":amount,"status":1,"createTime":trx_data["createtime"]}})
            cash_data = db_pool.b_cash_sweep.find_one({"_id":cash_detail_data["cash_sweep_id"]})
            if cash_data == None:
                logging.info("cash data is not exist error")
            else:
                db_pool.b_cash_sweep.update({"_id":cash_detail_data["cash_sweep_id"]},{"$set":{"status":2}})
    elif from_account == "btc_withdraw_test":
        #b_withdraw_transaction
        withdraw_data = db_pool.b_withdraw_transaction.find_one({"chainId":"btc","TransactionId":trx_data["trxid"]})
        if withdraw_data == None:
            db_pool.b_withdraw_transaction.insert({"chainId":"btc","TransactionId":trx_data["trxid"],"fromAddress":from_address,"toAddress":to_address,"assetName":"btc","amount":amount,"status":2,"trxTime":trx_data["trxTime"]})
        else:
            db_pool.b_withdraw_transaction.update({"chainId":"btc","TransactionId":trx_data["trxid"]},{"$set":{"status":2,"trxTime":trx_data["trxTime"]}})
    if to_account == "btc_test":
        #b_deposit_transaction
        deposit_data = db_pool.b_deposit_transaction.find_one({"chainId":"btc","TransactionId":trx_data["trxid"]})
        if deposit_data == None:
            db_pool.b_deposit_transaction.insert({"chainId":"btc","TransactionId":trx_data["trxid"],"fromAddress":from_address,"toAddress":to_address,"assetName":"btc","amount":amount,"blockNum":block_num,"trxTime":trx_data["trxTime"]})

    return trx_data


def update_block_trx_amount(db_pool,block_info):
    block = db_pool.b_block
    block.update({"blockHash":block_info.block_id},{"$set" : {"trxamount:":str(block_info.trx_amount),"trxfee":block_info.trx_fee}})



#采集数据
def collect_data_cb(db_pool):
    try:
        while GlobalVariable_btc.sync_start_per_round <= GlobalVariable_btc.sync_end_per_round:
            block_num_fetch = GlobalVariable_btc.sync_start_per_round
            GlobalVariable_btc.sync_start_per_round += 1

            # 采集块
            block_info = collect_block(db_pool, block_num_fetch)
            for trx_id in block_info.transactions:
                # 采集交易
                base_trx_data = get_transaction_data(trx_id)
                if base_trx_data == None:
                    continue
                pretty_trx_info = collect_pretty_transaction(db_pool, base_trx_data, block_info.block_num)
                # 统计块中交易总金额和总手续费
                for amount in pretty_trx_info["toAmounts"]:
                    block_info.trx_amount = block_info.trx_amount + amount
                for fee_amount in pretty_trx_info["trxFee"]:
                    block_info.trx_fee = block_info.trx_fee + fee_amount
            if block_info.trx_amount > 0 or -block_info.trx_fee > 0.0:
                update_block_trx_amount(db_pool, block_info)

        # 连接使用完毕，需要释放连接

    except Exception, ex:
        raise ex

