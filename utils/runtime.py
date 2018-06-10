#coding=utf8

'''runtime support'''

import redis
import hashids
import config

from altools.client import HttpClient

userapi_cli = HttpClient(config.USER_API)

hids = hashids.Hashids('qfpay')
