# coding: utf-8

#TODO, 暂未用到

from service import db
from utils import enums
from datetime import datetime, timedelta

def get_root_user():
  user = db.s_user.find_one({}, {'username': 'root'})
  if user is None:
    user = {
      'username': 'root',
      'email': 'root@root',
      'password': '123456', # TODO
      'realName': 'root',
      'phone': 'root',
      'address': '',
      'returnAddress': '',
      'userType': enums.UserTypes.SUPER_ADMIN,
      'deleted': False,
      'lastLoginTime': datetime.utcnow(),
      'createTime': datetime.utcnow(),
    }
    db.s_user.insert_one(user)
    user = db.s_user.find_one({}, {'username': 'root'})
  return user
