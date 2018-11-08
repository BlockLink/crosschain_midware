# -*- coding: utf-8 -*-

# from __future__ import print_function
import requests
import json
from config import config
import sys
import shutil
import os
from math import pow,floor
import time
from service import logger
import traceback

temp_config = config["development"]

def eth_request(method, args):
    url = "http://%s:%s" % (temp_config.ETH_URL, temp_config.ETH_PORT)
    request_template = '''{"id":"1","method":"%s","params":%s}'''
    args_str = json.dumps(args)
    data_to_send = request_template % (method, args_str)
    #print data_to_send

    payload = ""
    headers = {
        'Content-Type': "application/json"
    }
    response = requests.request("POST", url, data=data_to_send, headers=headers)
    test = response.text
    #print test
    response.close()
    return response.text


def eth_backup():
    # 只对Linux平台进行备份
    if sys.platform != 'linux2':
        return True
    backup_path = '/var/backup_keystore/'
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    ret = eth_request("admin_datadir", [])
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return False
    source_path = json_data["result"]

    shutil.copytree(source_path, backup_path)
    return True


def eth_create_address():
    address = ''
    data = {}
    # 写入数据库待做
    result = eth_request("personal_newAccount", [temp_config.ETH_SECRET_KEY])
    json_result = json.loads(result)
    if json_result.has_key("result"):
        address = json_result["result"]
        return address
    return address


def eth_get_base_balance(address):
    result = eth_request("eth_getBalance", [address, "latest"])
    print result
    json_result = json.loads(result)
    if json_result.get("result") is None:
        return 0
    amount = long(json_result["result"], 16)
    return float(amount / pow(10, 18))
    # return


def eth_get_no_precision_balance(address,last_block_num):
    result = eth_request("eth_getBalance", [address,  "latest"])
    print result
    json_result = json.loads(result)
    if json_result.get("result") is None:
        return 0
    amount = long(json_result["result"], 16)
    return amount
    # return


def get_account_list_from_wallet():
    addressList = []
    result = eth_request("personal_listAccounts", [])
    print type(result)
    print result
    json_result = json.loads(result)
    if json_result.has_key("result"):
        addressList = json_result["result"]
        return addressList
    return addressList


def get_transaction_data(trx_id):
    # print "\ntrx_id:",trx_id
    ret = eth_request("Service.GetTrx", [str(trx_id)])
    # print ret
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return None, None
    resp_data = json_data.get("result")
    ret = eth_request("Service.GetTrxReceipt", [str(trx_id)])
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return None, None
    receipt_data = json_data.get("result")
    return resp_data, receipt_data


#创建转账交易 默认GasPrice 5Gwei
def eth_send_transaction(from_address,to_address,value,gasPrice="0x1dcd6500",gas="0x76c0"):
    ret = eth_request("personal_unlockAccount",[from_address,temp_config.ETH_SECRET_KEY,1000])
    json_data = json.loads(ret)
    print ret
    if json_data.get("result") is None:
        return ''
    elif not json_data["result"]:
        return ''
    ret = eth_request("eth_sendTransaction", [{"from": from_address, "to": to_address,
                                               "value": hex(long(floor(float(float(value) * pow(10,18))))).replace('L', ''),
                                               "gas": gas, "gasPrice": gasPrice}])
    json_data = json.loads(ret)
    print ret
    if json_data.get("result") is None:
        return ""
    else:
        return json_data.get("result")
def get_contract_address(trxId):
    ret = eth_request("Service.GetTrxReceipt", [trxId])
    if json.loads(ret).get("result") != None:
        receipt = json.loads(ret).get("result")
        return receipt["contractAddress"]
    else:
        return ''
def checkHex(ch):
    if ch >='0'and ch<='9':
        return True
    if ch >='A'and ch<='F':
        return True
    if ch >='a'and ch<='f':
        return True
    return False
def eth_validate_address(addr):
    if len(addr) != 42:
        return False
    ret = True
    i = 0
    for item in addr:
        if i == 0:
            if item != '0':
                ret = False
                break
        if i == 1:
            if item != 'x':
                ret = False
                break
        if i > 1:
            if checkHex(item) == False:
                ret = False
                break
        i = i+1
    return ret
def eth_get_address_balance(address,chainId):
    if chainId == "eth":
        real_precision = 18
        ret = eth_request("Service.GetNormalBalance", [address])
    elif 'erc' in chainId:
        contract_addr = address['contract_addr']
        addr = address['addr']
        real_precision = address['precison']
        ret = eth_request("Service.GetErc20Balance", [[contract_addr,addr]])
        #print ret
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return '0'
    else:
        return str(float(int(json_data.get("result"), 16)) / pow(10, int(real_precision)))
def eth_get_trx_count(address,indexFormat):
    ret = eth_request("Service.GetTransactionCount",[[address,indexFormat]])
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return {}
    else:
        return json_data.get("result")

def add_guard_address(addr):
    if "erc" in addr:
        pos = addr.find("erc")
        handle_addr = addr[0:pos]
        eth_request("Service.AddNormalAddress",[handle_addr])
        eth_request("Service.AddErc20Address",[handle_addr])
    else:
        eth_request("Service.AddNormalAddress", [addr])
def eth_send_raw_transaction(param):
    ret = eth_request("Service.BroadcastRawTransaction",[param])
    json_data = json.loads(ret)
    print ret
    if json_data.get("result") is None:
        return ''
    else:
        return json_data.get("result")
def eth_verify_signed_message(addr, message, signature):
    ret = eth_request("Service.Personal_ecRecover",[[message,signature]])
    json_data = json.loads(ret)
    if json_data.get("result") != None:
        return json_data['result'].upper() == addr.upper()

    else:
        return False
def get_latest_block_num():
    ret = eth_request("eth_blockNumber",[])
    json_data = json.loads(ret)
    return int(json_data["result"],16)

def eth_collect_money(cash_sweep_account, accountList, safeBlock):
    try:
        result_data = {}
        result_data["errdata"] = []
        result_data["data"] = []
        print accountList
        last_block_num = get_latest_block_num() - int(safeBlock)
        # 存储创建成功的交易单号
        for account in accountList:
            amount = eth_get_no_precision_balance(account,last_block_num)

            print (float(amount) / pow(10, 18))
            print float(float(amount) / pow(10, 18)) > float(temp_config.ETH_Minimum)
            if float(float(amount) / pow(10, 18)) > float(temp_config.ETH_Minimum):
                print hex(long((amount - pow(10, 15)))).replace('L', '')
                # 转账给目标账户
                result = eth_request("personal_unlockAccount", [account, temp_config.ETH_SECRET_KEY, 10000])
                if json.loads(result).get("result") is None:
                    result_data["errdata"].append(
                        {"from_addr": account, "to_addr": cash_sweep_account, "amount": float(amount) / pow(10, 18),
                         "error_reason": u"账户解锁失败"})
                    # 写入归账失败的列表
                    continue

                ret = eth_request("eth_sendTransaction",[{"from": account, "to": cash_sweep_account,
                                                          "value": hex(long((amount - pow(10,15)))).replace('L',''),
                                                          "gas": "0x76c0", "gasPrice": "0x1dcd6500"}])
                if json.loads(result).get("result") is None:
                    result_data["errdata"].append(
                        {"from_addr": account, "to_addr": cash_sweep_account, "amount": float(amount) / pow(10, 18),
                         "error_reason": u"账户创建交易失败"})
                    # 写入归账失败的列表
                    continue
                else:
                    result_data["data"].append(
                        {"from_addr": account, "to_addr": cash_sweep_account, "amount": float(amount) / pow(10, 18),
                         "trx_id": json.loads(ret).get("result")})
                    # 获取交易详情按笔计入details
                    # 写入归账成功返回
        return result_data, None
    except Exception, ex:
        logger.info(traceback.format_exc())
        return None, ex.message


def eth_get_collect_money(accountList):
    # 从钱包获取归账地址列表
    result_data = dict()
    result_data["details"] = []

    total_amount = 0.0
    for account in accountList:
        amount = eth_get_base_balance(account)
        one_data = {}
        one_data["address"] = account
        one_data["amount"] = float(amount) / pow(10, 18)
        result_data["details"].append(one_data)
        total_amount += float(amount) / pow(10, 18)

    result_data["total_amount"] = total_amount
    return result_data


if __name__ == '__main__':
    add_guard_address("0x66c69ce0515edbd2ed7f299fb05a25065c3608d7erc")
    # get_account_list_from_wallet()
    # eth_create_address()
    # get_account_list_from_db()
    # eth_collect_money(2,"0x085aa94b764316d5e608335d13d926c6c6911e56")

