#!/usr/bin/env python
# encoding=utf8

from collect_btc_block import CacheManager
from collector_conf import HCCollectorConfig
from wallet_api import WalletApi
from collect_btc_block import BTCCoinTxCollector


class HCCoinTxCollecter(BTCCoinTxCollector):
    def __init__(self, db):
        super(HCCoinTxCollecter, self).__init__(db)
        self.t_multisig_address = self.db.b_hc_multisig_address
        self.config = HCCollectorConfig()
        conf = {"host": self.config.RPC_HOST, "port": self.config.RPC_PORT}
        self.wallet_api = WalletApi(self.config.ASSET_SYMBOL, conf)
        self.cache = CacheManager(self.config.SYNC_BLOCK_NUM, self.config.ASSET_SYMBOL)
