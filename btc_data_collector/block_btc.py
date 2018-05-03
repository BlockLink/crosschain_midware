#!/usr/bin/env python
# encoding: utf-8

__author__ = 'hasee'


from datetime import datetime


class BlockInfoBtc(object):
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
        self.block_bonus = 0.0
        # 块交易金额
        self.trx_amount = 0.0
        #块手续费
        self.trx_fee = 0.0


    def __cmp__(self, other):
        return cmp(self.block_num, other.block_num)


    def from_block_resp(self, block_result):
        self.block_id = (block_result.get("hash"))
        self.block_num = int(block_result.get("height"))
        self.block_size = int(block_result.get("size"))
        self.previous = (block_result.get("previousblockhash"))
        self.trx_digest = (block_result.get("merkleroot"))
        self.block_time = datetime.fromtimestamp(int(block_result.get("time")))
        self.transactions = block_result.get("tx")
        self.block_bonus = 5.0
        self.trx_count = len(self.transactions)
        self.amount = 0.0
        self.fee = 0.0

    def get_json_data(self):
        return {"blockHash":self.block_id,"chainId":"btc","blockNumber":self.block_num,"blockSize":self.block_size,
                "previous":self.previous,"trxDigest":self.trx_digest,"transactionsCount":self.trx_count,
        "trxamount":self.trx_amount,"trxfee":self.trx_fee,"createtime":datetime.now()}
#UT
'''test = BlockInfoBtc()
test.from_block_resp(btc_request("getblock",["002379afa908f31f31fd0ad139656aefdaec526af074db583acda9c679c5a536"])['result'])
print test.get_json_data()'''