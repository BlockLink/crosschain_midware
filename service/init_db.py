# coding: utf-8

from __future__ import print_function
from service import db
import pymongo

db.s_user.create_index([('email', pymongo.ALL)], unique=True)

db.b_block.create_index([('chainId', pymongo.ALL)])
db.b_block.create_index([('blockHash', pymongo.ALL)])

db.b_raw_transaction.create_index([('chainId', pymongo.ALL)])
db.b_raw_transaction.create_index([('trxId', pymongo.ALL)])

db.b_raw_transaction_input.create_index([('rawTransactionid', pymongo.ALL)])
db.b_raw_transaction_input.create_index([('address', pymongo.ALL)])

db.b_raw_transaction_output.create_index([('rawTransactionid', pymongo.ALL)])
db.b_raw_transaction_output.create_index([('address', pymongo.ALL)])

db.b_chain_account.create_index([('name', pymongo.ALL)])
db.b_chain_account.create_index([('address', pymongo.ALL)])
db.b_chain_account.create_index([('chainId', pymongo.ALL)])
db.b_chain_account.create_index([('creatorUserId', pymongo.ALL)])

db.b_deposit_transaction.create_index([('chainId', pymongo.ALL)])
db.b_deposit_transaction.create_index([('fromAddress', pymongo.ALL)])

db.b_withdraw_transaction.create_index([('chainId', pymongo.ALL)])
db.b_withdraw_transaction.create_index([('toAddress', pymongo.ALL)])
