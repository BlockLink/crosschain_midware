#!/usr/bin/env python
# encoding=utf8

import logging
import json
import time
from coin_tx_collector import CoinTxCollector
from collector_conf import BKCollectorConfig
from wallet_api import WalletApi

class BKCoinTxCollector(CoinTxCollector):
    std_offline_abi = [
        "dumpData",
        "owner",
        "owner_assets",
        "sell_orders",
        "sell_orders_num",
        "state"
    ]


    def __init__(self, db):
        super(BKCoinTxCollector, self).__init__()
        self.stop_flag = False
        self.db = db
        self.order_list = []
        self.config = BKCollectorConfig()
        conf = {"host": self.config.RPC_HOST, "port": self.config.RPC_PORT}
        self.wallet_api = WalletApi(self.config.ASSET_SYMBOL, conf)


    def do_collect_app(self):
        while self.stop_flag is False:
            self.collect_token_contract()
            time.sleep(10)
        return ""


    def collect_token_contract(self):
        ret = self.wallet_api.http_request("get_contract_storage_changed", [0])
        if not ret.has_key('result') or ret['result'] == None:
            logging.info("Get contract failed")
            return

        for c in ret["result"]:
            if self._check_contract_type(c["contract_address"]):
                self._get_token_contract_info(c["contract_address"], c["block_num"])
        if len(self.order_list) > 0:
            self.db.b_exchange_contracts.insert_many(self.order_list, ordered=False)
        self.order_list = []


    def _check_contract_type(self, contract_address):
        ret = self.wallet_api.http_request("get_contract_info", [contract_address])
        if ret['result'] == None:
            logging.info("Call get_contract_info error")
            return False
        offline_abi = ret['result']['code_printable']['offline_abi']
        for abi in BKCoinTxCollector.std_offline_abi:
            if offline_abi.index(abi) >= 0:
                logging.debug(abi)
            else:
                logging.info("Not standard token contract: " + abi)
                return False
        ret = self.wallet_api.http_request("invoke_contract_offline",
                                           [self.config.CONTRACT_CALLER, contract_address, "state", ""])
        if ret.has_key('result') and ret['result'] == "COMMON":
            logging.debug("Contract state is good: " + contract_address + " | " + ret['result'])
            return True
        else:
            logging.info("Contract state error: " + contract_address + " | " + ret['result'])
            return False


    def _get_token_contract_info(self, contract_address, block_num):
        ret = self.wallet_api.http_request("invoke_contract_offline",
                                           [self.config.CONTRACT_CALLER, contract_address, "sell_orders", ""])
        if ret['result'] == None:
            logging.info("get_contract_order error")
            return
        result = json.loads(ret['result'])
        if isinstance(result, dict):
            for k, v in result.items():
                [from_asset, to_asset] = k.split(',')
                order_info = json.loads(v)
                for o in order_info['orderArray']:
                    [from_supply, to_supply, price] = o.split(',')
                    self.order_list.append({"from_asset": from_asset, "to_asset": to_asset,
                                       "from_supply": from_supply, "to_supply": to_supply,
                                       "price": price, "contract_address": contract_address,
                                       "block_num": block_num})
        self.db.b_exchange_contracts.remove(
                {"contract_address": contract_address})
