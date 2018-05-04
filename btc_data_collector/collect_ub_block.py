#!/usr/bin/env python
# encoding=utf8


from collector_conf import UBCollectorConfig
from wallet_api import WalletApi
from collect_btc_block import BTCCoinTxCollector


class UBCoinTxCollecter(BTCCoinTxCollector):
    def __init__(self, db):
        super(UBCoinTxCollecter, self).__init__(db)
        self.t_multisig_address = self.db.b_ub_multisig_address
        self.config = UBCollectorConfig()
        conf = {"host": self.config.RPC_HOST, "port": self.config.RPC_PORT}
        self.wallet_api = WalletApi(self.config.ASSET_SYMBOL, conf)