# -*- coding: utf-8 -*-

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    ETH_SECRET_KEY = 'Q!wert123@'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_HOST = 'chaindb'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'
    ETH_SECRET_KEY = 'Q!wert123@'
    ETH_URL = 'eth_wallet'
    ETH_PORT = 8546
    ETH_Minimum = 1
    BTC_HOST = 'btc_wallet'
    BTC_PORT = 60011


class DaConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_HOST = '192.168.127.128'
    MONGO_PORT = 27017
    MONGO_NAME = 'test'
    BTC_HOST = 'btc_wallet'
    BTC_PORT = 60011


class SunnyConfig(Config):
    DEBUG = True

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_HOST = '192.168.1.121'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'
    ETH_SECRET_KEY = 'Q!wert123@'
    ETH_URL = '192.168.1.121'
    ETH_PORT = 8546
    ETH_Minimum = 1
    BTC_HOST = '192.168.1.104'
    BTC_PORT = 60011


class TestingConfig(Config):
    TESTING = True
    MONGO_HOST = 'chaindb'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'


class ProductionConfig(Config):
    MONGO_HOST = 'chaindb'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'


class hzkConfig(Config) :
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_HOST = '192.168.1.115'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'
    ETP_URL = '192.168.1.123'
    ETP_PORT = 8820
    ETH_Minimum = 1


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'Sunny': SunnyConfig,
    'Da': DaConfig,
    'hzk':hzkConfig
}
