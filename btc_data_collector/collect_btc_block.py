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
import leveldb
import time
import threading
import pybitcointools
import json
from block_btc import BlockInfoBtc
from datetime import datetime
from coin_tx_collector import CoinTxCollector
from collector_conf import BTCCollectorConfig
from wallet_api import WalletApi
from Queue import Queue


gLock = threading.Lock()
q = Queue()


class CacheManager(object):
    def __init__(self, sync_key, symbol):
        self.sync_key = sync_key
        self.multisig_address_cache = set()
        self.raw_transaction_cache = []
        self.block_cache = []
        self.withdraw_transaction_cache = []
        self.deposit_transaction_cache = []
        self.utxo_cache = {}
        self.utxo_flush_cache = {}
        self.utxo_spend_cache = set()
        self.flush_thread = None
        self.balance_unspent ={}
        self.balance_spent = {}
        self.symbol = symbol
        try:
            self.utxo_db_cache = leveldb.LevelDB('./utxo_db' + self.symbol)
        except Exception, ex:
            logging.error(ex)


    def get_utxo(self, utxo_id):
        if self.utxo_cache.has_key(utxo_id):
            return self.utxo_cache[utxo_id]
        if self.utxo_flush_cache.has_key(utxo_id):
            return self.utxo_flush_cache[utxo_id]
        try:
            db_data = self.utxo_db_cache.Get(utxo_id)
        except KeyError:
            db_data = None
        if db_data is not None:
            return json.loads(db_data)
        else:
            return None


    def spend_utxo(self, utxo_id):
        logging.debug("Spend utxo: " + utxo_id)
        self.utxo_spend_cache.add(utxo_id)
        data = self.get_utxo(utxo_id)
        if data is None:
            return
        addr = data.get("address")
        if self.balance_spent.has_key(addr) :
            self.balance_spent[addr].append(utxo_id)
        else:
            self.balance_spent[addr]=[utxo_id]


    def add_utxo(self, utxo_id, data):
        logging.debug("Add utxo: " + utxo_id)
        self.utxo_cache[utxo_id] = data
        addr = data.get("address")
        if self.balance_unspent.has_key(addr):
            self.balance_unspent[addr].append(utxo_id)
        else:
            self.balance_unspent[addr] = [utxo_id]


    def flush_to_db(self, db):
        blocks = self.block_cache
        raw_trasaction = self.raw_transaction_cache
        withdraw_transaction = self.withdraw_transaction_cache
        deposit_transaction = self.deposit_transaction_cache
        self.utxo_flush_cache = self.utxo_cache
        balance_unspent = self.balance_unspent
        balance_spent = self.balance_spent
        if self.flush_thread is not None:
            self.flush_thread.join()
            self.flush_thread = None
        self.flush_thread = threading.Thread(target=CacheManager.flush_process,
                                        args=(self.symbol,db, [
                                                  db.b_block,
                                                  db.raw_transaction_db,
                                                  db.b_deposit_transaction,
                                                  db.b_withdraw_transaction
                                              ],
                                              [
                                                  blocks,
                                                  raw_trasaction,
                                                  deposit_transaction,
                                                  withdraw_transaction
                                              ],
                                              self.utxo_flush_cache,
                                              self.utxo_spend_cache,
                                              self.utxo_db_cache,
                                              self.sync_key,
                                              balance_unspent,
                                              balance_spent))
        self.flush_thread.start()
        self.block_cache = []
        self.raw_transaction_cache = []
        self.withdraw_transaction_cache = []
        self.deposit_transaction_cache = []
        self.utxo_cache = {}
        self.utxo_spend_cache = set()
        self.balance_unspent = {}
        self.balance_spent = {}


    @staticmethod
    def flush_process(symbol,db, tables, data, utxo_cache, utxo_spend_cache, utxo_db, sync_key,balance_unspent,balance_spent):
        for i, t in enumerate(tables):
            if len(data[i]) > 0:
                logging.debug(data[i][0])
                t.insert(data[i])
        block_num = data[0][len(data[0])-1]["blockNumber"]
        logging.info(sync_key + ": " + str(block_num))

        #Flush utxo to leveldb
        batch = leveldb.WriteBatch()
        for key in utxo_spend_cache:
            batch.Delete(key)
        for key,value in utxo_cache.items():
            batch.Put(key, json.dumps(value))
        try:
            utxo_db.Write(batch, sync=True)
        except Exception,ex:
            print "flush db", ex
        bulk_unspent = db.b_balance_unspent.initialize_ordered_bulk_op()
        bulk_spent = db.b_balance_spent.initialize_ordered_bulk_op();
        #Flush balance to mongodb.
        nCount=0
        for addr,value in balance_unspent.items() :
            record = db.b_balance_unspent.find_one({"chainId": symbol.lower(), "address": addr},{"_id":0,"chainId": 1})
            if record is None:
                bulk_unspent.insert({'chainId': symbol.lower(), 'address': addr, "trxdata": value})
            else:
                bulk_unspent.find({"chainId": symbol.lower(), "address": addr}).update_one(
                                                         {"$addToSet": {"trxdata": {"$each": value}}})
            nCount+=1
            if nCount == 30 :
                bulk_unspent.execute()
                bulk_unspent = db.b_balance_unspent.initialize_ordered_bulk_op()
                nCount = 0
        if nCount != 0:
            bulk_unspent.execute()
            nCount=0
        for addr,value in balance_spent.items() :
            record = db.b_balance_spent.find_one({"chainId": symbol.lower(), "address": addr},
                                                   {"_id": 0, "chainId": 1})
            if record is None:
                bulk_spent.insert({'chainId': symbol.lower(), 'address': addr, "trxdata": value})
            else:
                bulk_spent.find({"chainId": symbol.lower(), "address": addr}).update_one(
                    {"$addToSet": {"trxdata": {"$each": value}}})
            nCount += 1
            if nCount == 30:
                bulk_spent.execute()
                bulk_spent = db.b_balance_spent.initialize_ordered_bulk_op()
                nCount = 0
        if nCount != 0:
            bulk_spent.execute()
            nCount = 0
        #Update sync block number finally.
        db.b_config.update({"key": sync_key}, {
            "$set": {"key": sync_key, "value": str(block_num)}})


class CollectBlockThread(threading.Thread):
    # self.config.ASSET_SYMBOL.lower()
    def __init__(self, db, config, wallet_api,sync_status):
        threading.Thread.__init__(self)
        self.stop_flag = False
        self.db = db
        self.config = config
        self.wallet_api = wallet_api
        self.last_sync_block_num = 0
        self.sync_status = sync_status


    def run(self):
        # 清理上一轮的垃圾数据，包括块数据、交易数据以及合约数据
        self.last_sync_block_num = self.clear_last_garbage_data()
        self.process_blocks()
    def get_sync_status(self):
        return self.sync_status
    def stop(self):
        self.stop_flag = True


    def clear_last_garbage_data(self):
        ret = self.db.b_config.find_one({"key": self.config.SYNC_BLOCK_NUM})
        if ret is None:
            return 0
        last_sync_block_num = int(ret["value"])
        try:
            self.db.b_raw_transaction.remove(
                {"blockNum": {"$gte": last_sync_block_num}, "chainId": self.config.ASSET_SYMBOL.lower()})
            self.db.b_block.remove(
                {"blockNumber": {"$gte": last_sync_block_num}, "chainId": self.config.ASSET_SYMBOL.lower()})
            self.db.b_raw_transaction_input.remove(
                {"blockNum": {"$gte": last_sync_block_num}, "chainId": self.config.ASSET_SYMBOL.lower()})
            self.db.b_raw_transaction_output.remove(
                {"blockNum": {"$gte": last_sync_block_num}, "chainId": self.config.ASSET_SYMBOL.lower()})
            self.db.b_deposit_transaction.remove(
                {"blockNum": {"$gte": last_sync_block_num}, "chainId": self.config.ASSET_SYMBOL.lower()})
            self.db.b_withdraw_transaction.remove(
                {"blockNum": {"$gte": last_sync_block_num}, "chainId": self.config.ASSET_SYMBOL.lower()})
        except Exception, ex:
            print ex
        return int(last_sync_block_num)


    def process_blocks(self):
        # 线程启动，设置为同步状态
        config_db = self.db.b_config
        config_db.update({"key": self.config.SYNC_STATE_FIELD},
                         {"key": self.config.SYNC_STATE_FIELD, "value": "true"})
        while self.stop_flag is False :
            self.latest_block_num = self._get_latest_block_num()
            if  self.last_sync_block_num >= self.latest_block_num :
                self.sync_status = False
                time.sleep(1)
                continue
            try:
                # 获取当前链上最新块号
                logging.debug("latest_block_num: %d, last_sync_block_num: %d" %
                              (self.latest_block_num, self.last_sync_block_num))
                if q.qsize() > 10:
                    logging.info(q.qsize())
                    time.sleep(1)
                    continue
                # Collect single block info
                block_info = self.collect_block(self.db, self.last_sync_block_num)
                q.put(block_info)
                self.last_sync_block_num += 1
                if self.last_sync_block_num % 20 == 0:
                    self._show_progress(self.last_sync_block_num, self.latest_block_num)
            except Exception, ex:
                logging.info(traceback.format_exc())
                print ex
                # 异常情况，60秒后重试
                time.sleep(60)
                self.process_blocks()


    #采集块数据
    def collect_block(self, db_pool, block_num_fetch):
        ret1 = self.wallet_api.http_request("getblockhash", [block_num_fetch])
        if ret1['result'] == None:
            raise Exception("blockchain_get_block error")
        block_hash = ret1['result']
        if self.config.ASSET_SYMBOL == "HC":
            ret2 = self.wallet_api.http_request("getblock", [str(block_hash)])
        else:
            ret2 = self.wallet_api.http_request("getblock", [str(block_hash), 2])
        if ret2['result'] == None:
            raise Exception("blockchain_get_block error")
        json_data = ret2['result']
        block_info = BlockInfoBtc()
        block_info.from_block_resp(json_data)
        logging.debug("Collect block [num:%d], [block_hash:%s], [tx_num:%d]" % (block_num_fetch, block_hash, len(json_data["tx"])))
        return block_info


    @staticmethod
    def _show_progress(current_block, total_block):
        sync_rate = float(current_block) / total_block
        sync_process = '#' * int(40 * sync_rate) + ' ' * (40 - int(40 * sync_rate))
        sys.stdout.write("\rsync block [%s][%d/%d], %.3f%%\n" % (sync_process, current_block, total_block, sync_rate * 100))


    def _get_latest_block_num(self):
        ret = self.wallet_api.http_request("getblockcount", [])
        real_block_num = ret['result']
        safe_block = 6
        safe_block_ret = self.db.b_config.find_one({"key": self.config.SAFE_BLOCK_FIELD})
        if safe_block_ret is not None:
            safe_block = int(safe_block_ret["value"])
        return int(real_block_num) - safe_block


class BTCCoinTxCollector(CoinTxCollector):
    sync_status = True

    def __init__(self, db):
        super(BTCCoinTxCollector, self).__init__()

        self.stop_flag = False
        self.db = db
        self.t_multisig_address = self.db.b_btc_multisig_address
        self.multisig_address_cache = set()
        self.config = BTCCollectorConfig()
        conf = {"host": self.config.RPC_HOST, "port": self.config.RPC_PORT}
        self.wallet_api = WalletApi(self.config.ASSET_SYMBOL, conf)
        self.cache = CacheManager(self.config.SYNC_BLOCK_NUM, self.config.ASSET_SYMBOL)


    def _update_cache(self):
        for addr in self.t_multisig_address.find({"addr_type": 0}):
            self.multisig_address_cache.add(addr["address"])


    def do_collect_app(self):
        self._update_cache()
        self.collect_thread = CollectBlockThread(self.db, self.config, self.wallet_api,self.sync_status)
        self.collect_thread.start()
        count = 0
        last_block = 0
        while self.stop_flag is False:

            count += 1
            block = q.get()
            if last_block >= block.block_num:
                logging.error("Unordered block number: " + str(last_block) + ":" + str(block.block_num))
            last_block = block.block_num
            # Update block table
            # t_block = self.db.b_block
            logging.debug("Block number: " + str(block.block_num) + ", Transaction number: " + str(len(block.transactions )))
            self.cache.block_cache.append(block.get_json_data())
            # Process each transaction
            for trx_data in block.transactions:
                logging.debug("Transaction: %s" % trx_data)
                if self.config.ASSET_SYMBOL == "HC":
                    if block.block_num == 0:
                        continue
                    trx_data = self.get_transaction_data(trx_data)
                pretty_trx_info = self.collect_pretty_transaction(self.db, trx_data, block.block_num)
            self.sync_status = self.collect_thread.get_sync_status()
            if  self.sync_status:
                logging.debug(str(count) + " blocks processed, flush to db")
                self.cache.flush_to_db(self.db)
            elif self.sync_status is False :
                self.cache.flush_to_db(self.db)
                self._update_cache()
                time.sleep(2)

        self.collect_thread.stop()
        self.collect_thread.join()


    def get_transaction_data(self, trx_id):
        ret = self.wallet_api.http_request("getrawtransaction", [trx_id, 1])
        if ret["result"] is None:
            resp_data = None
        else:
            resp_data = ret["result"]
        return resp_data


    def collect_pretty_transaction(self, db_pool, base_trx_data, block_num):
        trx_data = {}
        trx_data["chainId"] = self.config.ASSET_SYMBOL.lower()
        trx_data["trxid"] = base_trx_data["txid"]
        trx_data["blockNum"] = block_num
        vin = base_trx_data["vin"]
        vout = base_trx_data["vout"]
        trx_data["vout"] = []
        trx_data["vin"] = []
        # is_coinbase_trx = self.is_coinbase_transaction(base_trx_data)
        out_set = {}
        in_set = {}
        multisig_in_addr = ""
        multisig_out_addr = ""
        is_valid_tx = True

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
            if not trx_in.has_key('vout'):
                logging.error(trx_in)
            utxo_id = self._cal_UTXO_prefix(trx_in['txid'], trx_in['vout'])
            in_trx = self.cache.get_utxo(utxo_id)
            self.cache.spend_utxo(utxo_id)
            if in_trx is None:
                logging.info(
                    "Fail to get vin transaction [%s:%d] of [%s]" % (trx_in["txid"], trx_in['vout'], trx_data["trxid"]))
                if self.config.ASSET_SYMBOL == "HC":
                    ret1 = self.wallet_api.http_request("getrawtransaction", [trx_in['txid'], 2])
                else:
                    ret1 = self.wallet_api.http_request("getrawtransaction", [trx_in['txid'], True])
                if not ret1.has_key('result'):
                    logging.error("Fail to get vin transaction [%s:%d] of [%s]" % (trx_in["txid"], trx_in['vout'], trx_data["trxid"]))
                    exit(0)
                addr =  self._get_vout_address(ret1.get("result").get("vout")[int(trx_in['vout'])])
                if addr == "" :
                    continue
                if self.cache.balance_spent.has_key(addr):
                    self.cache.balance_spent[addr].append(utxo_id)
                else:
                    self.cache.balance_spent[addr] = [utxo_id]
                for t in ret1['result']['vout']:
                    if t['n'] == trx_in['vout']:
                        in_trx = {'address': self._get_vout_address(t), 'value': t['value']}
                        break

            in_address = in_trx["address"]
            if (in_set.has_key(in_address)):
                in_set[in_address] += in_trx["value"]
            else:
                in_set[in_address] = in_trx["value"]
            trx_data["vin"].append({"txid": trx_in["txid"], "vout": trx_in["vout"], "value": in_trx["value"], "address": in_address})
            if in_address in self.multisig_address_cache:
                if multisig_in_addr == "":
                    multisig_in_addr = in_address
                else:
                    if multisig_in_addr != in_address:
                        is_valid_tx = False
        for trx_out in vout:
            # Update UBXO cache
            if trx_out["scriptPubKey"]["type"] == "nonstandard":
                self.cache.add_utxo(
                    self._cal_UTXO_prefix(base_trx_data["txid"], trx_out["n"]),
                    {"address": "", "value": 0 if (not trx_out.has_key("value")) else trx_out["value"]})
            elif trx_out["scriptPubKey"].has_key("addresses"):
                address = self._get_vout_address(trx_out)
                self.cache.add_utxo(
                    self._cal_UTXO_prefix(base_trx_data["txid"], trx_out["n"]),
                    {"address": address, "value": 0 if (not trx_out.has_key("value")) else trx_out["value"]})
            # Check vout
            if trx_out["scriptPubKey"].has_key("addresses"):
                out_address = trx_out["scriptPubKey"]["addresses"][0]
                trx_data["vout"].append({"value": trx_out["value"], "n": trx_out["n"], "scriptPubKey": trx_out["scriptPubKey"]["hex"], "address": out_address})
                if in_set.has_key(out_address): # remove change
                    continue
                if (out_set.has_key(out_address)):
                    out_set[out_address] += trx_out["value"]
                else:
                    out_set[out_address] = trx_out["value"]
                if out_address in self.multisig_address_cache:
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
            logging.debug("Nothing to record")
            return

        #trx_data["trxTime"] = datetime.utcfromtimestamp(base_trx_data['time']).strftime("%Y-%m-%d %H:%M:%S")
        #trx_data["createtime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            self.cache.deposit_transaction_cache.append(deposit_data)
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
                self.cache.withdraw_transaction_cache.append(withdraw_data)

        # logging.info("add raw transaction")
        self.cache.raw_transaction_cache.append(trx_data)
        return trx_data


    def _cal_UTXO_prefix(self, txid, vout):
        return self.config.ASSET_SYMBOL + txid + "I" + str(vout)


    def _get_vout_address(self, vout_data):
        if vout_data["scriptPubKey"]["type"] == "multisig":
            address = pybitcointools.bin_to_b58check(pybitcointools.hash160(vout_data["scriptPubKey"]["hex"]),
                                                     self.config.MULTISIG_VERSION)
        elif vout_data["scriptPubKey"]["type"] == "witness_v0_scripthash" or vout_data["scriptPubKey"]["type"] == "witness_v0_keyhash":
            address = vout_data["scriptPubKey"]["hex"]
        else:
            if not vout_data["scriptPubKey"].has_key("addresses"):
                #ToDo: OP_ADD and other OP_CODE may add exectuing function
                return ""
            elif len(vout_data["scriptPubKey"]["addresses"]) > 1:
                logging.error("error data: ", vout_data)
                pass
            address = vout_data["scriptPubKey"]["addresses"][0]
        return address


    @staticmethod
    def _is_coinbase_transaction(trx_data):
        if len(trx_data["vin"]) == 1 and trx_data["vin"][0].has_key("coinbase"):
            return True
        return False

