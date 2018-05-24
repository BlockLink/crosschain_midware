# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger
from utils import error_utils
from datetime import datetime


@jsonrpc.method('Client.Upgrade.checkNewVersion(clientId=str, localVersion=str)')
def client_upgrade_check_new_version(clientId, localVersion):
    logger.info('Client.Upgrade.checkNewVersion')
    if type(clientId) != unicode:
        return error_utils.mismatched_parameter_type('clientId', 'STRING')
    if type(localVersion) != unicode:
        return error_utils.mismatched_parameter_type('localVersion', 'STRING')

    return {
        'clientId': clientId,
        'latestVersion': "1.0.5",
        'hasNewVersion': True,
        'downloadUrl': "",
        'checksum': ""
    }
