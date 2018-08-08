# -*- coding: utf-8 -*-
import requests
from base64 import encodestring
import json
from service import logger, app


def query(method, args):
    url = "http://%s:%s" % (app.config['QUERY_SERVICE_HOST'], app.config['QUERY_SERVICE_PORT'])
    user = 'a'
    passwd = 'b'
    basestr = encodestring('%s:%s' % (user, passwd))[:-1]
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

