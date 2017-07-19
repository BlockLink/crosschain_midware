#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'


import json
from datetime import datetime


class BlockInfo(object):
    def __init__(self):
        # 块hash
        self.block_id = ''
        # 块高度
        self.block_num = 0
        # 块大小
        self.block_size = 0
        # 上个块的块hash
        self.previous = ''
        # 块中交易信息摘要
        self.trx_digest = ''
        # 出块代理
        self.miner = ''
        # 出块时间
        self.block_time = ''
        # 块中交易
        self.transactions = []
        # 块中交易总数量
        self.trx_count = 0
        # 出块奖励
        self.block_bonus = 0
        # 块交易金额
        self.trx_amount = 0
        #块手续费
        self.trx_fee = 0


    def from_block_resp(self, block_result):
        self.block_id = (block_result.get("hash"))
        self.block_num = int(block_result.get("number"),16)
        self.block_size = int(block_result.get("size"),16)
        self.previous = (block_result.get("parentHash"))
        self.trx_digest = (block_result.get("transactionsRoot"))
        self.block_time = datetime.fromtimestamp(int(block_result.get("timestamp"),16)).strftime("%Y-%m-%d %H:%M:%S")
        self.transactions = block_result.get("transactions")
        self.block_bonus = 5.0
        self.trx_count = len(self.transactions)
        self.amount = 0.0
        self.fee = 0.0

    def get_json_data(self):
        return {"blockHash":self.block_id,"chainId":"eth","blockNumber":self.block_num,"blockSize":self.block_size,
                "previous":self.previous,"trxDigest":self.trx_digest,"transactionsCount":self.trx_count,
        "trxamount":self.trx_amount,"trxfee":self.trx_fee,"createtime":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
