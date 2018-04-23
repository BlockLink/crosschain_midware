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
import json
from collector_conf import BTCCollectorConfig
from wallet_api import WalletApi
import time
from block_btc import BlockInfoBtc
from datetime import datetime
from coin_tx_collector import CoinTxCollecter
from twisted.internet.defer import DeferredList, inlineCallbacks, returnValue,Deferred
from twisted.internet import reactor
import leveldb
import pybitcointools

class BTCCoinTxCollecter(CoinTxCollecter):
    def __init__(self, db):
        super(BTCCoinTxCollecter, self).__init__()
        self.db = db
        self.t_multisig_address = self.db.b_btc_multisig_address
        self.last_sync_block_num = 0
        self.sync_start_per_round = 0
        self.sync_end_per_round = 0
        self.current_sync_state = 0
        self.sync_limit_per_step = 10
        self.config = BTCCollectorConfig()
        self.utxo_cached = {}
        self.utxo_used_cache ={}
        self.utxo_delete = []
        self.untouch_count = 0
        self.handle_trx_count = 0
        self.address_trx_cache = {}
        self.multisig_address_cache={}
        self.start_time = time.time()
        self.sync_status = False
        self.block_cache = {}
        self.skip_analysis_block_num = 0
        self.leveldb = leveldb.LevelDB('./cache_utxo_db')

        conf = {"host": self.config.RPC_HOST, "port": self.config.RPC_PORT}
        self.wallet_api = WalletApi(self.config.ASSET_SYMBOL, conf)

    def flush_db(self):
        batch = leveldb.WriteBatch()
        for key,value in self.utxo_cached.items():
            #if self.utxo_delete.count(key):
            #    continue
            #print key,value
            batch.Put(key,json.dumps(value))
        for key in self.utxo_delete:
            batch.Delete(key)
        try:
            self.leveldb.Write(batch,sync=True)
        except Exception,ex:
            print "flush db",ex


        self.utxo_delete = []
        self.utxo_cached = {}
        self.utxo_used_cache = {}



    @inlineCallbacks
    def flush_block_db(self):
        block_db = self.db.b_block
        batch_add = []
        while True:
            try:
                cache_data = self.block_cache
                self.block_cache = {}
                for block_id, value in cache_data.items():
                    data = yield block_db.find_one_and_update({"chainId": self.config.ASSET_SYMBOL, "blockHash": block_id},
                                                                    {"$set": value} ,{"chainId":1})
                    if data is None:
                        batch_add.append(value)
                        if len(batch_add) > 1000:
                            yield block_db.insert_many(batch_add)
                            batch_add = []
                if len(batch_add)>0:
                    yield block_db.insert_many(batch_add)
                    batch_add = []
                if (len(self.block_cache) <1000 and self.sync_status == True) or (len(self.block_cache) ==0 and self.sync_status == False):
                    s = Deferred()
                    reactor.callLater(10, s.callback, None)
                    yield s
            except Exception,ex:
                print ex

    @inlineCallbacks
    def flush_mongo_db(self):
        address_trx_db = self.db.b_address_trx
        batch_add = []
        while True:
            cache_data = self.address_trx_cache
            self.address_trx_cache = {}

            for address, valuelist in cache_data.items():
                # print {"chainId": self.config.ASSET_SYMBOL, "address": address},{"$addToSet": {"trxdata": {"$each":valuelist}}},{"projection":{"chainId":1}}

                data = yield address_trx_db.find_one_and_update({"chainId": self.config.ASSET_SYMBOL, "address": address},
                                                                {"$addToSet": {"trxdata": {"$each": valuelist.values()}}},
                                                                {"chainId": 1})
                #print {"chainId": self.config.ASSET_SYMBOL, "address": address,
                #                      "trxdata": valuelist}
                if data is None:

                    batch_add.append({"chainId": self.config.ASSET_SYMBOL, "address": address,
                                      "trxdata": valuelist.values()})
                    if len(batch_add) > 1000:
                        yield address_trx_db.insert_many(batch_add)
                        batch_add = []
            if len(batch_add)>0:
                yield address_trx_db.insert_many(batch_add)
                batch_add = []
            if (len(self.address_trx_cache) <1000 and self.sync_status == True) or (len(self.address_trx_cache) ==0 and self.sync_status == False):
                s = Deferred()
                reactor.callLater(10, s.callback, None)
                yield s






    @inlineCallbacks
    def do_collect_app(self):
        while True:
            try:
                #程序启动，设置为同步状态
                config_db = self.db.b_config
                yield config_db.update({"key": self.config.SYNC_STATE_FIELD},
                                 {"key": self.config.SYNC_STATE_FIELD, "value": "true"})
                skip_data = yield config_db.find_one({"key":self.config.SKIP_ANALYSIS_BLOCK_NUM},{"value":1});
                if skip_data == None:
                    yield config_db.insert({"key": self.config.SKIP_ANALYSIS_BLOCK_NUM,"value":0});
                    self.skip_analysis_block_num =0
                else:
                    self.skip_analysis_block_num = skip_data["value"]
                self.sync_status = True
                # 清理上一轮的垃圾数据，包括块数据、交易数据以及合约数据
                self.last_sync_block_num = yield self.clear_last_garbage_data(self.db)
                print self.last_sync_block_num
                # 获取当前链上最新块号
                while True:
                    latest_block_num = yield self.get_latest_block_num()
                    logging.debug("latest_block_num: %d, last_sync_block_num: %d" % (latest_block_num, self.last_sync_block_num))
                    if self.last_sync_block_num >= latest_block_num:
                        self.sync_start_per_round = self.last_sync_block_num
                        self.sync_end_per_round = latest_block_num
                        self.current_sync_state = 1
                    else:
                        self.sync_start_per_round = self.last_sync_block_num
                        self.sync_end_per_round = ((
                                self.last_sync_block_num + self.config.SYNC_BLOCK_PER_ROUND) >= latest_block_num) \
                                and latest_block_num or (self.last_sync_block_num + self.config.SYNC_BLOCK_PER_ROUND)
                    logging.debug("This round start: %d, this round end: %d" % (self.sync_start_per_round, self.sync_end_per_round))

                    sync_rate = float(self.sync_start_per_round) / latest_block_num
                    sync_process = '#' * int(40 * sync_rate) + ' ' * (40 - int(40 * sync_rate))
                    sys.stdout.write(
                        "\rCurrent time: %s sync block [%s][%d/%d], %.3f%% \n" % (time.strftime('%Y-%m-%d %H:%M:%S'),sync_process, self.sync_start_per_round,
                                                              latest_block_num, sync_rate * 100))
                    if self.current_sync_state:
                        rpc_count = 1
                    else:
                        rpc_count = self.config.RPC_COROUTINE_MAX

                    multisig_cache = yield self.t_multisig_address.find({})
                    self.multisig_address_cache = {}
                    for mul_value in multisig_cache:
                        self.multisig_address_cache[mul_value["address"]] = mul_value["addr_type"]


                    defer_list = [self.collect_data_cb(self.db) for _ in range(rpc_count)]
                    yield DeferredList(defer_list)

                    self.last_sync_block_num = self.sync_start_per_round
                    self.flush_db()
                    yield config_db.update({"key": self.config.SYNC_BLOCK_NUM}, {
                        "$set": {"key": self.config.SYNC_BLOCK_NUM, "value": str(self.last_sync_block_num)}})

                    print "handle trx count:", self.handle_trx_count
                    print "untouch trx count", self.untouch_count
                    print "hadle trx per sec:", self.handle_trx_count/(time.time() - self.start_time)
                    if self.sync_start_per_round == latest_block_num + 1:
                        break

                d = yield config_db.update({"key": self.config.SYNC_STATE_FIELD}, {"key": self.config.SYNC_STATE_FIELD, "value": False})
                yield d
                self.sync_status = False

                # 同步结束，维护一个定时启动的任务去获取新产生的块
                sys.stdout.write("\n")
                s = Deferred()
                reactor.callLater(10, s.callback, None)
                yield s

            except Exception, ex:
                logging.error(traceback.format_exc())
                sys.stdout.write("\n")
                s = Deferred()
                reactor.callLater(60, s.callback, None)
                yield s


    @inlineCallbacks
    def get_latest_block_num(self):
        ret = yield self.wallet_api.http_request("getblockcount", [])
        real_block_num = ret['result']
        safe_block = 6
        safe_block_ret = yield self.db.b_config.find_one({"key": self.config.SAFE_BLOCK_FIELD})
        if safe_block_ret is not None:
            safe_block = int(safe_block_ret["value"])

        returnValue( int(real_block_num) - safe_block)


    @inlineCallbacks
    def clear_last_garbage_data(self, db_pool):
        ret =yield db_pool.b_config.find_one({"key": self.config.SYNC_BLOCK_NUM})
        if ret is None:
            returnValue(0)
        last_sync_block_num = int(ret["value"])
        try:
            yield db_pool.b_raw_transaction.remove({"blockNum":{"$gte": last_sync_block_num},"chainId": self.config.ASSET_SYMBOL.lower()})
            yield db_pool.b_block.remove({"blockNumber":{"$gte": last_sync_block_num},"chainId": self.config.ASSET_SYMBOL.lower()})
            yield db_pool.b_raw_transaction_input.remove({"blockNum": {"$gte": last_sync_block_num},"chainId": self.config.ASSET_SYMBOL.lower()})
            yield db_pool.b_raw_transaction_output.remove({"blockNum": {"$gte": last_sync_block_num},"chainId": self.config.ASSET_SYMBOL.lower()})
            yield db_pool.b_deposit_transaction.remove({"blockNum": {"$gte": last_sync_block_num},"chainId": self.config.ASSET_SYMBOL.lower()})
            yield db_pool.b_withdraw_transaction.remove({"blockNum": {"$gte": last_sync_block_num},"chainId": self.config.ASSET_SYMBOL.lower()})
        except Exception,ex:
            print ex
        returnValue( int(last_sync_block_num))


    #采集块数据
    @inlineCallbacks
    def collect_block(self, db_pool, block_num_fetch):
        try:
            ret1 = yield self.wallet_api.http_request("getblockhash", [block_num_fetch])
            if ret1['result'] == None:
                raise Exception("blockchain_get_block error")
            block_hash = ret1['result']
            ret2 = yield self.wallet_api.http_request("getblock", [str(block_hash),2])
            if ret2['result'] == None:
                raise Exception("blockchain_get_block error")
            json_data = ret2['result']
            block_info = BlockInfoBtc()
            block_info.from_block_resp(json_data)
            block = db_pool.b_block
            self.block_cache[block_info.block_id]=block_info.get_json_data(self.config.ASSET_SYMBOL)
            '''
            mongo_data = yield block.find_one({"blockHash":block_info.block_id})

            if mongo_data == None:
                yield block.insert(block_info.get_json_data())
            else:
                yield block.update({"blockHash":block_info.block_id},{"$set":block_info.get_json_data()})

            
            '''
            logging.debug("Collect block [num:%d], [block_hash:%s], [tx_num:%d]" % (
            block_num_fetch, block_hash, len(json_data["tx"])))
            returnValue( block_info)
        except Exception,ex:
            print ex
            logging.error(traceback.format_exc())

    @inlineCallbacks
    def get_transaction_data(self, trx_id):

        ret =yield self.wallet_api.http_request("getrawtransaction", [trx_id, True])
        if ret["result"] is None:
            resp_data = None
        else:
            resp_data = ret["result"]
        returnValue( resp_data)

    def is_coinbase_transaction(self,base_trx_data):
        if len(base_trx_data["vin"]) == 1 and base_trx_data["vin"][0].has_key("coinbase"):
            return True
        return False

    def cal_UTXO_prefix(self,txid,vout):
        return self.config.ASSET_SYMBOL+txid+"I"+str(vout)

    @inlineCallbacks
    def spend_UTXO(self,vin):
        '''search for all cache data if not find search database.if also not find query trx and decode that.'''
        txid = vin["txid"]
        vout = vin["vout"]
        utxo_prefix = self.cal_UTXO_prefix(txid,vout)

        count =0
        while True:
            if self.utxo_cached.has_key(utxo_prefix):
                cached_value = self.utxo_cached.pop(utxo_prefix)
                self.utxo_used_cache[utxo_prefix] = cached_value
                # print cached_value
                returnValue(cached_value)
            try:
                db_data = self.leveldb.Get(utxo_prefix)
            except KeyError:
                # print "spend_UTXO error"
                db_data = None
            if db_data is None:
                # db not found. then query trx from wallet
                if count % 100 == 99:
                    # db not found. then query trx from wallet
                    trx_data = yield self.get_transaction_data(txid)
                    print "untouch:", txid
                    self.untouch_count += 1
                    for vout_data in trx_data["vout"]:
                        if vout_data.has_key("scriptPubKey"):
                            if vout_data["scriptPubKey"]["type"] == "nonstandard":
                                self.utxo_cached[self.cal_UTXO_prefix(txid, vout_data["n"])] = {
                                    "address": "", "value": 0 if (not vout_data.has_key("value")) else vout_data["value"]}
                            elif vout_data["scriptPubKey"].has_key("addresses"):
                                address = self.get_vout_address(txid, vout_data)
                                self.utxo_cached[self.cal_UTXO_prefix(txid, vout_data["n"])] = {
                                    "address": address, "value": 0 if (not vout_data.has_key("value")) else vout_data["value"]}
                        #if vout_data["n"] == vout:
                        #    self.utxo_delete.append(utxo_prefix)
                        #    result = {"address":self.get_vout_address(trx_data, vout_data),"value":vout_data["value"]}
                        #    self.utxo_used_cache[utxo_prefix] = result
                         #   returnValue(result)
                count +=1
                if count %100 ==0:
                    print "wait count",count,utxo_prefix
                s = Deferred()
                reactor.callLater(0.5, s.callback, None)
                yield s
            else:
                self.utxo_delete.append(utxo_prefix)
                temp_json_data = json.loads(db_data)
                self.utxo_used_cache[utxo_prefix] = temp_json_data
                returnValue(temp_json_data)


        '''
        if self.utxo_cached.has_key(utxo_prefix):
            cached_value = self.utxo_cached.pop(utxo_prefix)
            #print cached_value
            returnValue(cached_value)
        try:
            db_data = self.leveldb.Get(utxo_prefix)
        except KeyError:
            #print "spend_UTXO error"
            db_data = None
        if db_data is None:
            # db not found. then query trx from wallet
            trx_data = yield self.get_transaction_data(txid)
            print "untouch:",txid
            self.untouch_count +=1
            for vout_data in trx_data["vout"]:
                if vout_data["n"] == vout:
                    self.utxo_delete.append(utxo_prefix)
                    returnValue(self.get_vout_address(trx_data,vout_data))
        else:
            self.utxo_delete.append(utxo_prefix)
            returnValue(db_data)
        '''

    def store_trx_mongo(self,db_pool,address,trxid,block_num,trx_index):

        if self.address_trx_cache.has_key(address):
            self.address_trx_cache[address][trxid]={"trxid":trxid,"block_num":block_num,"trx_index":trx_index}
        else:
            self.address_trx_cache[address] = {trxid:{"trxid":trxid,"block_num":block_num,"trx_index":trx_index}}

        #address_trx_db = db_pool.b_address_trx
        #address_record = yield address_trx_db.find_one({"chainId": self.config.ASSET_SYMBOL, "address": address},{"chainId" : 1, "address" : 1})
        #if address_record is None:
        #    yield address_trx_db.insert({"chainId": self.config.ASSET_SYMBOL, "address": address,
        #                                 "trxdata": [{"trxid":trxid,"block_num":block_num,"trx_index":trx_index}]})
        #else:

        #    yield address_trx_db.update({"chainId": self.config.ASSET_SYMBOL, "address": address},
        #                                {"$addToSet": {"trxdata": {"trxid":trxid,"block_num":block_num,"trx_index":trx_index}}})


    def get_vout_address(self,base_trx_data,vout_data):
        if vout_data["scriptPubKey"]["type"] == "multisig":
            address = pybitcointools.bin_to_b58check(pybitcointools.hash160(vout_data["scriptPubKey"]["hex"]),
                                                     self.config.MULTISIG_VERSION)
        else:
            if not vout_data["scriptPubKey"].has_key("addresses"):
                #ToDo: OP_ADD and other OP_CODE may add exectuing function
                return ""

            if len(vout_data["scriptPubKey"]["addresses"]) > 1:
                print "error data:", base_trx_data
            address = vout_data["scriptPubKey"]["addresses"][0]
        return address

    @inlineCallbacks
    def collect_all_transaction(self,db_pool,base_trx_data,block_num,trx_index):
        '''if the trx is coinbase trx then store all the vout
        and then store address to trx_id relationship'''
        #address_trx_db = db_pool.b_address_trx
        #temp_time = time.time()
        if self.is_coinbase_transaction(base_trx_data):
            for vout in base_trx_data["vout"]:
                if vout.has_key("scriptPubKey"):
                    if vout["scriptPubKey"]["type"] == "nonstandard":
                        self.utxo_cached[self.cal_UTXO_prefix(base_trx_data["txid"], vout["n"])] = {"address":"","value":0 if(not vout.has_key("value")) else vout["value"] }
                    elif vout["scriptPubKey"].has_key("addresses"):
                        address = self.get_vout_address(base_trx_data,vout)
                        self.utxo_cached[self.cal_UTXO_prefix(base_trx_data["txid"], vout["n"])] ={"address":address,"value":0 if(not vout.has_key("value")) else vout["value"] }
                        self.store_trx_mongo(db_pool,address,base_trx_data["txid"],block_num,trx_index)

        #'''else is normal trx, then spend the vin and store the vout'''
        else:
            for vin in base_trx_data["vin"]:
                relationship_address = yield self.spend_UTXO(vin)
                self.store_trx_mongo(db_pool,relationship_address["address"],base_trx_data["txid"],block_num,trx_index)

            for vout in base_trx_data["vout"]:
                if vout["scriptPubKey"]["type"] == "nonstandard":
                    self.utxo_cached[self.cal_UTXO_prefix(base_trx_data["txid"], vout["n"])] = {"address":"","value":0 if(not vout.has_key("value")) else vout["value"] }
                elif vout["scriptPubKey"].has_key("addresses"):

                    address = self.get_vout_address(base_trx_data,vout)
                    self.utxo_cached[self.cal_UTXO_prefix(base_trx_data["txid"], vout["n"])] = {"address":address,"value":0 if(not vout.has_key("value")) else vout["value"] }
                    self.store_trx_mongo(db_pool,address,base_trx_data["txid"],block_num,trx_index)
        #print "collect_all_transaction cost time:", time.time() - temp_time










    @inlineCallbacks
    def collect_pretty_transaction(self, db_pool, base_trx_data, block_num, trx_index):
        raw_transaction_db = db_pool.b_raw_transaction
        trx_data = {}
        trx_data["chainId"] = self.config.ASSET_SYMBOL.lower()
        trx_data["trxid"] = base_trx_data["txid"]
        trx_data["blockNum"] = block_num
        vin = base_trx_data["vin"]
        vout = base_trx_data["vout"]
        trx_data["vout"] = []
        trx_data["vin"] = []

        out_set = {}
        in_set = {}
        multisig_in_addr = ""
        multisig_out_addr = ""
        is_valid_tx = True
        logging.debug(base_trx_data)

        '''
        The corresponding relationship of the collection address to the transaction ID will be stored in the database.
        1. cache current utxo for trx_id vout address
        2. append address to transaction id relationship to current database.
        3. store queried trx data to database.
        4. calculate address balance and cache that.
        '''

        yield self.collect_all_transaction(db_pool, base_trx_data, block_num,trx_index)
        #temp_time = time.time()
        if block_num<self.skip_analysis_block_num:
            return
        """
        Only 3 types of transactions will be filtered out and be record in database.
        1. deposit transaction (vin contains only one no LINK address and vout contains only one LINK address)
        2. withdraw transaction (vin contains only one LINK address and vout contains no other LINK address)
        3. transaction between hot-wallet and cold-wallet (vin contains only one LINK address and vout contains only one other LINK address)

        Check logic:
        1. check all tx in vin and store addresses & values (if more than one LINK address set invalid)
        2. check all tx in vout and store all non-change addresses & values (if more than one LINK address set invalid)
        3. above logic filter out the situation - more than one LINK address in vin or vout but there is one condition
           should be filter out - more than one normal address in vin for deposit transaction
        4. then we can record the transaction according to transaction type
           only one other addres in vin and only one LINK address in vout - deposit
           only one LINK addres in vin and only other addresses in vout - withdraw
           only one LINK addres in vin and only one other LINK address in vout - transaction between hot-wallet and cold-wallet
           no LINK address in vin and no LINK address in vout - transaction that we don't care about, record nothing
        5. record original transaction in raw table if we care about it.
        """
        for trx_in in vin:
            if not trx_in.has_key("txid"):
                continue
            vin_prefix = self.cal_UTXO_prefix(trx_in["txid"],trx_in["vout"])
            if not self.utxo_used_cache.has_key(vin_prefix):
                logging.error("Fail to get vin transaction [%s] of [%s] from utxo use cached" % (trx_in["txid"], trx_data["trxid"]))

            else:
                in_trx = self.utxo_used_cache[vin_prefix]  # yield self.get_transaction_data(trx_in["txid"])
                logging.debug(in_trx)

                if in_trx["address"] !="":
                    in_address = in_trx["address"]
                    if (in_set.has_key(in_address)):
                        in_set[in_address] += in_trx["value"]
                    else:
                        in_set[in_address] = in_trx["value"]
                    trx_data["vin"].append({"txid": trx_in["txid"], "vout": trx_in["vout"], "value": in_trx["value"], "address": in_address})
                    if self.multisig_address_cache.has_key(in_address)and self.multisig_address_cache[in_address]==0:
                        if multisig_in_addr == "":
                            multisig_in_addr = in_address
                        else:
                            if multisig_in_addr != in_address:
                                is_valid_tx = False
                        break

        for trx_out in vout:
            if trx_out["scriptPubKey"].has_key("addresses"):
                out_address = trx_out["scriptPubKey"]["addresses"][0]
                trx_data["vout"].append({"value": trx_out["value"], "n": trx_out["n"], "scriptPubKey": trx_out["scriptPubKey"]["hex"], "address": out_address})
                if in_set.has_key(out_address): # remove change
                    continue
                if (out_set.has_key(out_address)):
                    out_set[out_address] += trx_out["value"]
                else:
                    out_set[out_address] = trx_out["value"]
                if self.multisig_address_cache.has_key(out_address) and self.multisig_address_cache[out_address]==0:
                    if multisig_out_addr == "":
                        multisig_out_addr = out_address
                    else:
                        is_valid_tx = False

        if not multisig_in_addr == "" and not multisig_out_addr == "": # maybe transfer between hot-wallet and cold-wallet
            if not is_valid_tx:
                logging.error("Invalid transaction between hot-wallet and cold-wallet")
                trx_data['type'] = -3
            else:
                trx_data['type'] = 0
        elif not multisig_in_addr == "": # maybe withdraw
            if not is_valid_tx:
                logging.error("Invalid withdraw transaction")
                trx_data['type'] = -1
            else:
                trx_data['type'] = 1
        elif not multisig_out_addr == "": # maybe deposit
            if not is_valid_tx or not len(in_set) == 1:
                logging.error("Invalid deposit transaction")
                trx_data['type'] = -2
            else:
                trx_data['type'] = 2
        else:
            logging.info("Nothing to record")
           # print "collect_pretty_transaction cost time:", time.time() - temp_time
            return
        trx_data["trxTime"] = datetime.utcfromtimestamp(base_trx_data['time']).strftime("%Y-%m-%d %H:%M:%S")
        trx_data["createtime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if trx_data['type'] == 2 or trx_data['type'] == 0:
            deposit_data = {
                "txid": base_trx_data["txid"],
                "from_account": in_set.keys()[0],
                "to_account": multisig_out_addr,
                "amount": str(out_set.values()[0]),
                "asset_symbol": self.config.ASSET_SYMBOL,
                "blockNum": block_num,
                "chainId": self.config.ASSET_SYMBOL.lower()
            }
            mongo_data = yield db_pool.b_deposit_transaction.find_one({"txid": base_trx_data["txid"]},{"txid":1})
            if mongo_data == None:
                yield db_pool.b_deposit_transaction.insert(deposit_data)
            else:
                yield db_pool.b_deposit_transaction.update({"trxid": base_trx_data["txid"]}, {"$set": deposit_data})
        elif trx_data['type'] == 1:
            for k, v in out_set.items():
                withdraw_data = {
                    "txid": base_trx_data["txid"],
                    "from_account": multisig_in_addr,
                    "to_account": k,
                    "amount": str(v),
                    "asset_symbol": self.config.ASSET_SYMBOL,
                    "blockNum": block_num,
                    "chainId": self.config.ASSET_SYMBOL.lower()
                }
                mongo_data = yield db_pool.b_withdraw_transaction.find_one({"txid": base_trx_data["txid"], "from_account": multisig_in_addr, "to_account": k, "blockNum": block_num},{"txid":1})
                if mongo_data == None:
                    yield db_pool.b_withdraw_transaction.insert(withdraw_data)
                else:
                    yield db_pool.b_withdraw_transaction.update({"trxid": base_trx_data["txid"], "from_account": multisig_in_addr, "to_account": k, "blockNum": block_num}, {"$set": withdraw_data})

        mongo_data = yield raw_transaction_db.find_one({"trxid": base_trx_data["txid"]},{"trxid":1})
        if mongo_data == None:
            yield raw_transaction_db.insert(trx_data)
        else:
            yield raw_transaction_db.update({"trxid": base_trx_data["txid"]}, {"$set": trx_data})

        returnValue(trx_data)

    @inlineCallbacks
    def update_block_trx_amount(self, db_pool, block_info):
        block = db_pool.b_block
        yield block.update({"blockHash":block_info.block_id},{"$set" : {"trxamount:":str(block_info.trx_amount),"trxfee":block_info.trx_fee}})


    #采集数据
    @inlineCallbacks
    def collect_data_cb(self, db_pool):
        try:
            while self.sync_start_per_round <= self.sync_end_per_round:
                block_num_fetch = self.sync_start_per_round
                self.sync_start_per_round += 1
                temp_time = time.time()
                # 采集块
                block_info = yield self.collect_block(db_pool, block_num_fetch)
                #print "block num: ",block_info.block_num , "   trx count: ",len(block_info.transactions)
                trx_index = 0
                for trx_data in block_info.transactions:

                    # 采集交易
                    #base_trx_data = yield self.get_transaction_data(trx_id)
                    #if base_trx_data is None:
                     #   continue
                    #logging.debug("Transaction: %s" % base_trx_data)
                   # print trx_data
                    pretty_trx_info = yield self.collect_pretty_transaction(db_pool, trx_data, block_info.block_num, trx_index)
                    trx_index += 1
                    self.handle_trx_count +=1
                #print "block num: ",block_info.block_num,"  cost time: ",time.time() -temp_time
            # 连接使用完毕，需要释放连接

        except Exception, ex:
            print ex

            logging.error(traceback.format_exc())
            raise ex

