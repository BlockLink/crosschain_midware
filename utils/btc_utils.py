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
def btc_query_tx_out(addr):
    message="[\""+addr+"\"]"
    resp = btc_request("listunspent",[1,9999999,message])
    if resp["result"] != None:
        return resp["result"]
    else:
        return None
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

def btc_get_transaction(trxid):
    resp = btc_request("getrawtransaction", [trxid])
    if resp["result"] != None:
        return btc_decode_hex_transaction(resp["result"])
    return ""


def btc_create_transaction(from_addr, redeemScript,to_addr, amount):
    txout = btc_query_tx_out(from_addr)
    if txout == None :
        return ""
    sum = 0.0
    vin_need =[]
    fee = 0.001
    for out in txout :
        if sum >= amount+fee:
            break
        sum+=int(out.get("amount"))
        vin_need.append(out)
    if sum < amount+fee:
        return ""
    vins=[]
    for need in vin_need :
        vin={'txid':need.get('txid'),'vout':need.get('vout'),'scriptPubKey':need.get('scriptPubKey')}
        vins.append(vin)
    #set a fee
    resp = ""
    if sum-amount == fee:
        resp = btc_request("createrawtransaction", [vins, {'%s' % to_addr: amount}])
    else:
        resp = btc_request("createrawtransaction", [vins,{'%s'%to_addr: amount,'%s'%from_addr:sum-amount-fee}])
    if resp["result"] != None:
        trx_hex = resp['result']
        trx = btc_decode_hex_transaction(trx_hex)
        return {"trx":trx,"hex":trx_hex}
    return ""

def btc_combineTrx(signatures) :
    resp = btc_request("combinerawtransaction",[signatures])
    if resp["result"] is None:
        return ""
    return {"hex":resp["result"]}

def btc_sign_transaction(addr,redeemScript,trx_hex):
    resp = btc_request("dumpprivkey",[addr])
    if resp["result"] is None :
        return ""
    prikey = resp["result"]
    resp = btc_decode_hex_transaction(trx_hex)
    vins = resp.get("vin")
    sign_vins=[]
    for vin in vins:
        ret = btc_request("gettxout",[vin.get('txid'),vin.get('vout')])
        if ret.get("result") is None:
            return ""
        ret = ret.get("result")
        sign_vins.append({"txid":vin.get('txid'),"vout":vin.get('vout'),"scriptPubKey":ret.get("scriptPubKey").get("hex"),"redeemScript": redeemScript})
            #"54210204cf519681cc19aa9a9fea60b641daecae99d48bce37570ec4a141eec1d16b87210376d1033db8ca28a837394f8280d8982620668c609aa1692baca1496a294271c42103bc770094d5fe4f2be6eeb7db1c7ee4c29315d75f9da15abea4d2f9dfee9578462102ca5209ff1d0cfbaeeb1ff7511a089110e0da3ea8f9e11f5a38c7a198b2c6d8f3210215e01b25a3d10919e335267f6b95ad5dab4589659cee33983e3cf97e80f13ad721030f610c3a4cad41c87eec4aa1dc40ab0ca8cd3cd8338156da076defa03ed057db2103065d0cd3c5f1f21394200597e4fa56ce676a91ad8c26f5fe8d87dd8afbea947b57ae"})
    resp = btc_request("signrawtransaction", [trx_hex,sign_vins,[prikey]])
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
