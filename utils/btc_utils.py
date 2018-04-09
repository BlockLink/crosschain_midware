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
        try:
            btc_request("importaddress", [resp["result"].get("address"),"",False])
        except:
            pass
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
    resp = btc_request("getnewaddress", [""])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address
def btc_validate_address(addr):
    resp = btc_request("validateaddress", [addr])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address

def btc_query_tx_out(addr):
    message=[addr]
    resp = btc_request("listunspent",[0,9999999,message])
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
def btc_import_addr(addr):
    btc_request("importaddress",[addr,"",False])

def btc_create_transaction(from_addr,dest_info):
    txout = btc_query_tx_out(from_addr)
    if txout == None :
        return ""
    sum = 0.0
    vin_need =[]
    fee = 0.001
    amount =0.0
    vouts ={}
    for addr,num in dest_info.items() :
        amount = round(amount + num,8)
        vouts[addr]=round(num,8)

    for out in txout :
        if sum >= round(amount+fee,8):
            break
        sum = round(sum +float(out.get("amount")),8)
        vin_need.append(out)
    if sum < round(amount+fee,8):
        return ""
    vins=[]
    script=[]
    for need in vin_need :
        pubkey = need.get("scriptPubKey")
        script.append(pubkey)
        vin={'txid':need.get('txid'),'vout':need.get('vout'),'scriptPubKey':pubkey}
        vins.append(vin)
    #set a fee
    resp = ""
    if round(sum-amount,8) == fee:
        resp = btc_request("createrawtransaction", [vins, vouts])
    else:
        vouts[from_addr]=round(sum-amount-fee,8)
        resp = btc_request("createrawtransaction", [vins,vouts])
    if resp["result"] != None:
        trx_hex = resp['result']
        trx = btc_decode_hex_transaction(trx_hex)
        return {"trx":trx,"hex":trx_hex,"scriptPubKey":script}
    return ""


def btc_combineTrx(signatures) :
    resp = btc_request("combinerawtransaction",[signatures])
    if resp["result"] is None:
        return ""
    trx = btc_decode_hex_transaction(resp["result"])
    return {"hex":resp["result"],"trx":trx}


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


def btc_backup_wallet():
    btc_request("backupwallet", ["/var/backup_keystore/btc_wallet.dat"])


def btc_get_withdraw_balance():
    rep = btc_request("getbalance", ["btc_withdraw_test"])
    balance = 0.0
    if rep["result"] != None:
        balance = rep["result"]
    return balance
