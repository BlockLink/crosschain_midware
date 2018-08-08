# -*- coding: utf-8 -*-

import os
from service import jsonrpc
from config import logger, config
from utils import error_utils
from flask import Flask, send_from_directory
from . import app
from datetime import datetime


@app.route("/download/<path:filename>", methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config["DOWNLOAD_PATH"], filename, as_attachment=True)


@jsonrpc.method('Client.Upgrade.checkNewVersion(clientId=str, localVersion=str)')
def client_upgrade_check_new_version(clientId, localVersion):
    logger.info('Client.Upgrade.checkNewVersion')
    if type(clientId) != unicode:
        return error_utils.mismatched_parameter_type('clientId', 'STRING')
    if type(localVersion) != unicode:
        return error_utils.mismatched_parameter_type('localVersion', 'STRING')


    return {
        'clientId': clientId,
        'downloadUrl': "/download/blocklink_wallet_upgrade.xml"
    }
