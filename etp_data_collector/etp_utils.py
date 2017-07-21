# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime
from collector_conf import ETP_PORT,ETP_URL


def etp_request(method, args):
    url = "http://%s:%s/rpc"%(ETP_URL,ETP_PORT)
    request_template = '''{"jsonrpc":"2.0","id":"1","method":"%s","params":%s}'''
    args_j = json.dumps(args)
    data_to_send = request_template % (method, args_j)
    headers = {
        'content-type': "application/x-www-form-urlencoded"
    }

    response = requests.request("POST", url, data=data_to_send, headers=headers)
    return response.text





if __name__ == '__main__':
    block_num = etp_request("fetch-height",[])

    header = (etp_request("fetch-header",["-t",int(15309)]))
    print header
    #print etp_request("getblock",[header.get('result').get("hash"),True])
    #print etp_request("fetch-utxo",["1","M8xiHzAwoXhAYSXoLK9MR2ZiunTDi3D5R9"])
    print etp_request("fetch-tx",['e8a4171f460946e5e423ddb92185d981f2f374959fa9d5ef673b94c541128772'])
    #res = json.loads(ret)
    #print res.get('txs')
