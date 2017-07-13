# coding: utf-8

def error_response(msg, code=40999):
    return {
        'error_code': code,
        'error_message': msg,
    }

# 错误码使用5-6位正整数

def mismatched_parameter_type(v, t):
    return error_response(u'%s should be stored in %s.' % (v, t), 40001)

def invalid_trx_type(v):
    return error_response(u'invalid transaction type: %s.' % v, 40002)

def invalid_chainId_type(v):
    return error_response(u'invalid chainId type: %s (eth, btc).' % v, 40003)