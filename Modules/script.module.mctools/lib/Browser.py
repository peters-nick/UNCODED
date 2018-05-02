# coding: utf-8
import re
import urllib2
from cookielib import LWPCookieJar
from urllib import urlencode
from logger import log
from json import loads

__author__ = 'Mancuniancol'

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36" \
             " (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36"


# provider web browser with cookies management
class Browser:
    _cookies = None
    cookies = LWPCookieJar()
    content = None
    status = None
    headers = ""

    def __init__(self):
        pass

    @classmethod
    def create_cookies(cls, payload):

        cls._cookies = urlencode(payload)

    # to open any web page
    @classmethod
    def open(cls, url='', language='en', post_data=None, get_data=None):
        if post_data is None:
            post_data = {}
        if get_data is not None:
            url += '?' + urlencode(get_data)
        print(url)
        result = True
        if len(post_data) > 0:
            cls.create_cookies(post_data)
        if cls._cookies is not None:
            req = urllib2.Request(url, cls._cookies)
            cls._cookies = None
        else:
            req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Content-Language', language)
        req.add_header("Accept-Encoding", "gzip")
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cls.cookies))  # open cookie jar
        try:
            response = opener.open(req)  # send cookies and open url
            cls.headers = response.headers
            # borrow from provider.py Steeve
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                cls.content = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response.read())
            else:
                cls.content = response.read()
            response.close()
            cls.status = 200
        except urllib2.HTTPError as e:
            cls.status = e.code
            result = False
        except urllib2.URLError as e:
            cls.status = e.reason
            result = False
        log.debug("Status: " + str(cls.status))
        log.debug(cls.content)
        return result

    # alternative when it is problem with https
    @classmethod
    def open2(cls, url=''):
        import httplib

        word = url.split("://")
        pos = word[1].find("/")
        conn = httplib.HTTPConnection(re.search[:pos])
        conn.request("GET", re.search[pos:])
        r1 = conn.getresponse()
        cls.status = str(r1.status) + " " + r1.reason
        cls.content = r1.read()
        if r1.status == 200:
            return True
        else:
            return False

    # used for sites with login
    @classmethod
    def login(cls, url, payload, word):
        result = False
        cls.create_cookies(payload)
        if cls.open(url):
            result = True
            data = cls.content
            if word in data:
                cls.status = 'Wrong Username or Password'
                result = False
        return result

    def json(self):
        return loads(self.content)
