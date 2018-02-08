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
from base import GlobalVariable_btc
from btc_utils import btc_request
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
            GlobalVariable_btc.sync_limit_per_step = 10

            # 获取当前链上最新块号
            while True:
                latest_block_num = get_latest_block_num(db)
                logging.debug("latest_block_num: %d, GlobalVariable_btc.last_sync_block_num: %d" % (latest_block_num, GlobalVariable_btc.last_sync_block_num))
                if GlobalVariable_btc.last_sync_block_num >= latest_block_num:
                    GlobalVariable_btc.sync_start_per_round = latest_block_num
                    GlobalVariable_btc.sync_end_per_round = latest_block_num
                else:
                    GlobalVariable_btc.sync_start_per_round = GlobalVariable_btc.last_sync_block_num
                    GlobalVariable_btc.sync_end_per_round = ((
                                                         GlobalVariable_btc.last_sync_block_num + SYNC_BLOCK_PER_ROUND) >= latest_block_num) \
                                                        and latest_block_num or (
                                                        GlobalVariable_btc.last_sync_block_num + SYNC_BLOCK_PER_ROUND)
                logging.debug("This round start: %d, this round end: %d" % (GlobalVariable_btc.sync_start_per_round, GlobalVariable_btc.sync_end_per_round))

                sync_rate = float(GlobalVariable_btc.sync_start_per_round) / latest_block_num
                sync_process = '#' * int(40 * sync_rate) + ' ' * (40 - int(40 * sync_rate))
                sys.stdout.write(
                    "\rsync block [%s][%d/%d], %.3f%%\n" % (sync_process, GlobalVariable_btc.sync_start_per_round,
                                                          latest_block_num, sync_rate * 100))
                while GlobalVariable_btc.sync_start_per_round <=GlobalVariable_btc.sync_end_per_round:
                    logging.debug("Start collect step from %d" % GlobalVariable_btc.sync_start_per_round)
                    collect_data_cb(db)
                    GlobalVariable_btc.last_sync_block_num = GlobalVariable_btc.sync_start_per_round
                    config.update({"key": "btcsyncblocknum"}, {"$set":{"key": "btcsyncblocknum", "value": str(GlobalVariable_btc.last_sync_block_num)}})

                if GlobalVariable_btc.sync_start_per_round == latest_block_num + 1:
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
    safe_block = 6
    safe_block_ret = db.b_config.find_one({"key":"btcsafeblock"})
    if safe_block_ret is not None:
        safe_block = int(safe_block_ret["value"])

    return int(real_block_num) - safe_block


def clear_last_garbage_data(db_pool):
    config = db_pool.b_config
    ret = config.find_one({"key":"btcsyncblocknum"})
    if ret is None:
        return 0
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
    block_info = BlockInfoBtc()
    block_info.from_block_resp(json_data)
    block = db_pool.b_block
    mongo_data = block.find_one({"blockHash":block_info.block_id})

    if mongo_data == None:
        block.insert(block_info.get_json_data())
    else:
        block.update({"blockHash":block_info.block_id},{"$set":block_info.get_json_data()})

    logging.debug("Collect block [num:%d], [block_hash:%s], [tx_num:%d]" % (block_num_fetch, block_hash, len(json_data["tx"])))

    return block_info


def get_transaction_data(trx_id):

    ret = btc_request("getrawtransaction",[trx_id, True])
    if ret["result"] is None:
        resp_data = None
    else:
        resp_data = ret["result"]
    return resp_data


def collect_pretty_transaction(db_pool, base_trx_data, block_num):
    #处理交易
    raw_transaction_db = db_pool.b_raw_transaction

    trx_data = {}
    trx_data["chainId"] = "btc"
    trx_data["trxid"] = base_trx_data["txid"]
    trx_data["blockNum"] = block_num
    vin = base_trx_data["vin"]
    vout = base_trx_data["vout"]
    trx_data["vout"] = []
    trx_data["vin"] = []

    # Process deposit transaction.
    multisig_in = False
    multisig_out = False
    out_set = {}
    in_set = {}
    deposit_in = ""
    deposit_out = ""
    logging.debug(base_trx_data)
    for trx_out in vout:
        if trx_out["scriptPubKey"].has_key("addresses"):
            out_address = trx_out["scriptPubKey"]["addresses"][0]
            trx_data["vout"].append({"value": trx_out["value"], "n": trx_out["n"], "scriptPubKey": trx_out["scriptPubKey"]["hex"], "address": out_address})
            if db_pool.b_btc_multisig_address.find_one({"address": out_address, "addr_type": 0}) is not None:
                if (out_set.has_key(out_address)):
                    out_set[out_address] += trx_out["value"]
                else:
                    out_set[out_address] = trx_out["value"]
                multisig_out = True     # maybe deposit
                deposit_out = out_address
        
    for trx_in in vin:
        if not trx_in.has_key("txid"):
            continue
        in_trx = get_transaction_data(trx_in["txid"])
        if in_trx is None:
            logging.error("Fail to get vin transaction [%s] of [%s]" % trx_in["txid"], trx_data["trxid"])
        else:
            logging.debug(in_trx)
            for t in in_trx["vout"]:
                if t["n"] == trx_in["vout"] and t["scriptPubKey"].has_key("addresses"):
                    in_address = t["scriptPubKey"]["addresses"][0]
                    if (in_set.has_key(in_address)):
                        in_set[in_address] += t["value"]
                    else:
                        in_set[in_address] = t["value"]
                    trx_data["vin"].append({"txid": trx_in["txid"], "vout": trx_in["vout"], "value": t["value"], "address": in_address})
                    if db_pool.b_btc_multisig_address.find_one({"address": in_address, "addr_type": 0}) is not None:
                        multisig_in = True
                    deposit_in = in_address
                    break

    if multisig_in and multisig_out: # maybe transfer between hot-wallet and cold-wallet
        if not len(in_set) == 1 or not len(out_set) == 1::
            logging.error("Invalid transaction between hot-wallet and cold-wallet")
            trx_data['type'] = -3
        else:
            trx_data['type'] = 0
    elif multisig_in: # maybe withdraw
        if not len(in_set) == 1:
            logging.error("Invalid withdraw transaction, withdraw from multi-address")
            trx_data['type'] = -1
        else:
            db_pool.b_withdraw_transaction.insert(trx_data)
            trx_data['type'] = 1
    elif multisig_out: # maybe deposit
        if not len(in_set) == 1:
            logging.error("Invalid deposit transaction, deposit from multi-address")
            trx_data['type'] = -2
        elif not len(out_set) == 1:
            logging.error("Invalid deposit transaction, deposit to multi-address")
            trx_data['type'] = -4
        else:
            trx_data['type'] = 2
    else:
        logging.info("Nothing to record")
        return
    trx_data["trxTime"] = datetime.utcfromtimestamp(base_trx_data['time']).strftime("%Y-%m-%d %H:%M:%S")
    trx_data["createtime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if trx_data['type'] == 2 or trx_data['type'] == 0:
        mongo_data = db_pool.b_deposit_transaction.find_one({"txid": base_trx_data["txid"]})
        deposit_data = {
            "txid": base_trx_data["txid"],
            "from_account": deposit_in,
            "to_account": deposit_out,
            "amount": str(out_set[deposit_out]),
            "asset_symbol": "BTC",
            "blockNum": block_num,
            "chainId":"btc"
        }
        if mongo_data == None:
            db_pool.b_deposit_transaction.insert(deposit_data)
        else:
            db_pool.b_deposit_transaction.update({"trxid": base_trx_data["txid"]}, {"$set": deposit_data})

    mongo_data = raw_transaction_db.find_one({"trxid": base_trx_data["txid"]})
    if mongo_data == None:
        raw_transaction_db.insert(trx_data)
    else:
        raw_transaction_db.update({"trxid": base_trx_data["txid"]}, {"$set": trx_data})

    return trx_data


def update_block_trx_amount(db_pool,block_info):
    block = db_pool.b_block
    block.update({"blockHash":block_info.block_id},{"$set" : {"trxamount:":str(block_info.trx_amount),"trxfee":block_info.trx_fee}})



#采集数据
def collect_data_cb(db_pool):
    try:
        count = 0
        while GlobalVariable_btc.sync_start_per_round <= GlobalVariable_btc.sync_end_per_round and count < GlobalVariable_btc.sync_limit_per_step:
            block_num_fetch = GlobalVariable_btc.sync_start_per_round

            # 采集块
            block_info = collect_block(db_pool, block_num_fetch)
            for trx_id in block_info.transactions:
                # 采集交易
                base_trx_data = get_transaction_data(trx_id)
                if base_trx_data is None:
                    continue
                logging.debug("Transaction: %s" % base_trx_data)
                pretty_trx_info = collect_pretty_transaction(db_pool, base_trx_data, block_info.block_num)
            GlobalVariable_btc.sync_start_per_round += 1
            count += 1

        # 连接使用完毕，需要释放连接

    except Exception, ex:
        raise ex

