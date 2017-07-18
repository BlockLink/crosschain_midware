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

def invalid_chainid_type(v):
    return error_response(u'invalid chainId type: %s (eth, btc).' % v, 40003)

def mis_cash_sweep_config():
    return error_response(u'cash sweep address config not exists.', 40004)

def mis_cash_sweep_address(address):
    return error_response(u'[%s] cash sweep address not set.'% address, 40005)

def invalid_deposit_address(address):
    return error_response(u'address [%s] is not in deposit address list '%address, 40006)

def invaild_eth_address(address):
    return error_response(u'address [%s] not start with 0x '%address, 40007)

def empty_cash_sweep_id():
    return error_response(u'opId is empty', 40008)

def unexcept_error(ex):
    return error_response('chain happend unexcept error %s'%ex,49999)

