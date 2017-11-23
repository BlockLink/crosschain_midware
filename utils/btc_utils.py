# -*- coding: utf-8 -*-
import requests
from base64 import encodestring
import json
from service import logger, app
import traceback


def btc_request(method, args):
    url = "http://%s:%s" % (app.config['BTC_HOST'], app.config['BTC_PORT'])
    user = 'a'
    passwd = 'b'
    basestr = encodestring('%s:%s' % (user, passwd))[:-1]
    '''x = []
    for arg in args:
        x.append(arg)'''
    args_j = json.dumps(args)
    payload = "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
    headers = {
        'content-type': "text/plain",
        'authorization': "Basic %s" % (basestr),
        'cache-control': "no-cache",
    }
    logger.info(payload)
    response = requests.request("POST", url, data=payload, headers=headers)
    rep = response.json()
    logger.info(rep)
    return rep


def btc_create_multisig(addrs, amount):
    resp = btc_request("createmultisig", [amount, addrs])
    if resp["result"] != None:
        return resp["result"]
    else:
        return None

def btc_add_multisig(addrs, amount):
    resp = btc_request("addmultisigaddress", [amount, addrs])
    if resp["result"] != None:
        return resp["result"]
    else:
        return None

def btc_validate_address(addr):
    resp = btc_request("validateaddress", [addr])
    if resp["result"] != None:
        return resp["result"]
    else:
        return None

def btc_create_address():
    resp = btc_request("getnewaddress", ["btc_test"])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address

def btc_broadcaset_trx(trx):
    resp = btc_request("sendrawtransaction", [trx])
    result = ""
    if resp["result"] != None:
        result = resp["result"]
    return result

def btc_sign_message(addr, message):
    resp = btc_request("signmessage", [addr, message])
    signed_message = ""
    if resp["result"] != None:
        signed_message = resp["result"]
    return signed_message

def btc_verify_signed_message(addr, message, signature):
    resp = btc_request("verifymessage", [addr, signature, message])
    result = False
    if resp["result"] != None:
        result = resp["result"]
    return result
def btc_decode_hex_transaction(trx_hex):
    resp = btc_request("decoderawtransaction",[trx_hex])
    if resp["result"] is not None :
        return resp["result"]
    return ""
def btc_create_transaction(from_addr, to_addr, amount):
    resp = btc_request("createrawtransaction", [[{'txid':'d253cf22e4cfb18dfea319c2f60154705eba8b00f0a7bf0ef11cadbd67cc5ff4','vout':0}],{'%s'%to_addr: 44.027}])
    trx_hex = ""
    if resp["result"] != None:
        trx_hex = resp["result"]
    return trx_hex

def btc_sign_transaction(trx_hex):
    resp = btc_request("signrawtransaction", [trx_hex,
        [{"txid":"d253cf22e4cfb18dfea319c2f60154705eba8b00f0a7bf0ef11cadbd67cc5ff4","vout":0,"scriptPubKey":"a914762b215e246c36ec8a05c5b11e0ec1a81a4115dc87", "redeemScript": "522102cafafab50491678c9f676e0bd0fb3ff3130ccf033b230665eea6aabc1f81696521022bab1af9bb4adccc8db0c81a3c2abf09fb53f4f77d3bae040e498d4f7ed38fff52ae"}]])
    trx_hex = ""
    if resp["result"] != None:
        trx_hex = resp["result"]
    return trx_hex

def btc_create_withdraw_address():
    resp = btc_request("getnewaddress", ["btc_withdraw_test"])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address


def btc_collect_money(address, safe_block):
    try:
        result_data = {}
        result_data["errdata"] = []
        result_data["data"] = []
        resp = btc_request("settxfee", [0.0004])
        if resp["result"] == None:
            raise Exception("settxfee error")
        resp = btc_request("getbalance", ["btc_test", safe_block])
        if resp["result"] == None:
            raise Exception("getbalance error")
        balance = resp["result"]
        if balance - 0.0005 <= 0:
            raise Exception("balance is not enough error")
        fee_need = 0.0005
        params = ["btc_test", address, balance - fee_need]
        resp = btc_request("sendfrom", params)
        if resp["result"] == None:
            if resp["error"] != None:
                if resp["error"]["message"] != None:
                    errs = resp["error"]["message"]
                    start = errs.find("Error: This transaction requires a transaction fee of at least ")
                    if start != -1:
                        fee_need = float(errs[len("Error: This transaction requires a transaction fee of at least "):]) + 0.0001
                        if balance - fee_need <= 0:
                            raise Exception("balance is not enough error")
                        params = ["btc_test", address, balance - fee_need]
                        resp = btc_request("sendfrom", params)
                        if resp["result"] == None:
                            raise Exception(resp)
                    else:
                        raise Exception(resp)
                else:
                    raise Exception(resp)
            else:
                raise Exception(resp)
        result_data["data"].append(
            {"from_addr": "btc_test", "to_addr": address, "amount": balance - fee_need, "trx_id": resp["result"]})
        return result_data, None
    except Exception, ex:
        logger.info(traceback.format_exc())
        return None, ex.message


def btc_withdraw_to_address(address, amount):
    try:
        result_data = {}
        result_data["errdata"] = []
        result_data["data"] = []
        resp = btc_request("settxfee", [0.0004])
        if resp["result"] == None:
            raise Exception("settxfee error")
        resp = btc_request("getbalance", ["btc_withdraw_test"])
        if resp["result"] == None:
            raise Exception("getbalance error")
        balance = resp["result"]
        if balance - amount - 0.0005 <= 0:
            raise Exception("balance is not enough error")
        params = ["btc_withdraw_test", address, amount]
        resp = btc_request("sendfrom", params)
        if resp["result"] == None:
            raise Exception(resp)
        result_data["data"].append(
            {"from_addr": "btc_withdraw_test", "to_addr": address, "amount": amount, "trx_id": resp["result"]})
        return resp["result"]
    except Exception, ex:
        logger.info(traceback.format_exc())
        return ""


'''def get_account_list_btc_address():
    btc_request("getaddressesbyaccount",["btc_test"])'''


def btc_backup_wallet():
    btc_request("backupwallet", ["/var/backup_keystore/btc_wallet.dat"])


def btc_get_deposit_balance():
    rep = btc_request("getbalance", ["btc_test"])
    balance = 0.0
    if rep["result"] != None:
        balance = rep["result"]
    return balance


def btc_get_withdraw_balance():
    rep = btc_request("getbalance", ["btc_withdraw_test"])
    balance = 0.0
    if rep["result"] != None:
        balance = rep["result"]
    return balance
    # btc_collect_money("1ERjyPUWpDH7mLmAHZzwCJ6jsn4tyHfj2Y")
