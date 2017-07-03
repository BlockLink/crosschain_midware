# coding: utf-8

# from service import db
from mongoengine import *
from datetime import datetime, timedelta


class BChainAccount(Document):
  meta = {'collection': 'b_chain_account'}
  chainId = StringField(max_length=100, required=True)
  name = StringField(max_length=100, required=True)
  address = StringField(max_length=200, required=True)
  securedPrivateKey = StringField(max_length=500, required=False)
  creatorUserId = ObjectIdField(required=False)
  balance = DictField(required=True)
  memo = StringField(max_length=1000, default='', required=False)
  createTime = DateTimeField(default=datetime.now, required=True)
  updateTime = DateTimeField(default=datetime.now, required=True)



