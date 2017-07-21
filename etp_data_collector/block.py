#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'


import json
from datetime import datetime
import time

def timestamp_datetime(value):
    format = '%Y-%m-%d %H:%M:%S'
    # value为传入的值为时间戳(整形)，如：1332888820
    value = time.localtime(value)
    ## 经过localtime转换后变成
    ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
    # 最后再经过strftime函数转换为正常日期格式。
    dt = time.strftime(format, value)
    return dt

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


    def from_header_resp(self, header_result):
        header_result = header_result.get('result')
        self.block_id = (header_result.get("hash"))
        self.block_num = int(header_result.get("number"))
        #self.block_size = int(header_result.get("size"),16)
        self.previous = (header_result.get("previous_block_hash"))
        #self.trx_digest = (block_result.get("transactionsRoot"))
        self.block_time = timestamp_datetime(float(header_result.get("time_stamp")))


    def from_trx_resp(self,trxs):
        if trxs is None:
            return
        bonus_trx=trxs[0]
        self.block_bonus = float(bonus_trx.get('outputs')[0].get('value'))/float(100000000)
        for trx in trxs :
            self.transactions.append(trx.get('hash'))
            if bonus_trx.get('hash') == trx.get('hash') :
                continue
          #####
            pass

    def get_json_data(self):
        return {"blockHash": self.block_id, "chainId": "etp", "blockNumber": self.block_num,
                "previous": self.previous, "trxDigest": self.trx_digest, "transactionsCount": self.trx_count
            ,"block_bonus":self.block_bonus, "createtime": self.block_time}





class TransactionInfo :
    def __init__(self):
        self.chainId = ''
        self.trxid = ''
        self.blockid = ''
        self.blockNum = ''
        self.fromAddresses = []
        self.fromAmounts = []
        self.toAmounts = []
        self.toAssets = []
        self.trxFee = float(0)
        self.FeeAsset = []
        self.isSpecialTransaction = False
        self.transactionJsonInfo = ''
        self.memo = ''
        self.trxTime = ''
        self.createtime = ''
        self.isDispatched = 0
        self.isHandled = 0
