# coding: utf-8

import logging
import logging.handlers
import os


def get_logger():
  level = logging.DEBUG
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s[%(lineno)d] - %(funcName)s - %(message)s')
  logger = logging.getLogger(__name__)
  logger.setLevel(level)
  ch = logging.StreamHandler()
  ch.setLevel(level)
  ch.setFormatter(formatter)
  logger.addHandler(ch)
  log_file_path = 'logs/contract_platform.log'
  if not os.path.exists(os.path.dirname(log_file_path)):
    os.mkdir(os.path.dirname(log_file_path))
  ch_file = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=10000000, backupCount=5)
  ch_file.setLevel(logging.DEBUG)
  ch_file.setFormatter(formatter)
  logger.addHandler(ch_file)
  return logger


logger = get_logger()
