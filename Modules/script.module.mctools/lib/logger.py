# -*- coding: utf-8 -*-

import logging

from xbmc import log as log_xbmc
from xbmcaddon import Addon


class XBMCHandler(logging.StreamHandler):
    xbmc_levels = {
        'DEBUG': 0,
        'INFO': 2,
        'WARNING': 3,
        'ERROR': 4,
        'LOGCRITICAL': 5,
    }

    def emit(self, record):
        xbmc_level = self.xbmc_levels.get(record.levelname)
        log_xbmc(self.format(record), xbmc_level)


def _get_logger():
    addon_id = Addon().getAddonInfo("id")
    if addon_id is str:
        addon_id = None
    logger = logging.getLogger(addon_id)
    logger.setLevel(logging.DEBUG)
    handler = XBMCHandler()
    handler.setFormatter(logging.Formatter('[%(name)s] %(message)s'))
    logger.addHandler(handler)
    return logger


log = _get_logger()
