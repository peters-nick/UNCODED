# -*- coding: utf-8 -*-

import re


class Magnet:
    def __init__(self, magnet):
        self.magnet = magnet + '&'
        # hash
        info_hash = re.search('urn:btih:(.*?)&', self.magnet)
        result = ''
        if info_hash is not None:
            result = info_hash.group(1)
        self.info_hash = result
        # name
        name = re.search('dn=(.*?)&', self.magnet)
        result = ''
        if name is not None:
            result = name.group(1).replace('+', ' ')
        self.name = result.title()
        # trackers
        self.trackers = re.findall('tr=(.*?)&', self.magnet)


def get_int(text):
    # noinspection PyBroadException
    try:
        value = int(re.search('([0-9]*\.[0-9]+|[0-9]+)', text).group(0))
    except:
        value = 0
    return value


# noinspection PyBroadException
def size_int(size_txt):
    try:
        return int(size_txt)
    except:
        size_txt = size_txt.upper()
        size1 = size_txt.replace('B', '').replace('I', '').replace('K', '').replace('M', '').replace('G', '')
        size = get_float(size1)
        if 'K' in size_txt:
            size *= 1000
        if 'M' in size_txt:
            size *= 1000000
        if 'G' in size_txt:
            size *= 1e9
        return get_int(size)


def get_float(text):
    # noinspection PyBroadException
    try:
        value = float(re.search('([0-9]*\.[0-9]+|[0-9]+)', text).group(0))
    except:
        value = 0
    return value


# Convert all the &# codes to char, remove extra-space and normalize
def uncode_name(name):
    from HTMLParser import HTMLParser
    name = name.replace('<![CDATA[', '').replace(']]', '')
    name = HTMLParser().unescape(name)
    return name
