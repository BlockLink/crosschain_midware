# coding: utf-8

from __future__ import print_function
from service import db
import pymongo

db.s_user.create_index([('email', pymongo.ALL)], unique=True, dropDups=1)
db.s_user.create_index([('username', pymongo.ALL)], unique=True, dropDups=1)

db.b_block.create_index([('chainId', pymongo.ALL)], dropDups=1)
db.b_block.create_index([('blockHash', pymongo.ALL)], dropDups=1)

db.b_raw_transaction.create_index([('chainId', pymongo.ALL)], dropDups=1)
db.b_raw_transaction.create_index([('trxId', pymongo.ALL)], dropDups=1)

db.b_raw_transaction_input.create_index([('rawTransactionid', pymongo.ALL)], dropDups=1)
db.b_raw_transaction_input.create_index([('address', pymongo.ALL)], dropDups=1)

db.b_raw_transaction_output.create_index([('rawTransactionid', pymongo.ALL)], dropDups=1)
db.b_raw_transaction_output.create_index([('address', pymongo.ALL)], dropDups=1)

db.b_chain_account.create_index([('name', pymongo.ALL)], dropDups=1)
db.b_chain_account.create_index([('address', pymongo.ALL)], dropDups=1)
db.b_chain_account.create_index([('chainId', pymongo.ALL)], dropDups=1)
db.b_chain_account.create_index([('creatorUserId', pymongo.ALL)], dropDups=1)
db.b_chain_account.create_index([('chainId', pymongo.TEXT), ('address', pymongo.TEXT)], unique=True, dropDups=1)

db.b_deposit_transaction.create_index([('chainId', pymongo.ALL)], dropDups=1)
db.b_deposit_transaction.create_index([('fromAddress', pymongo.ALL)], dropDups=1)

db.b_withdraw_transaction.create_index([('chainId', pymongo.ALL)], dropDups=1)
db.b_withdraw_transaction.create_index([('toAddress', pymongo.ALL)], dropDups=1)

