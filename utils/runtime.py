#coding=utf8

'''runtime support'''

import redis
import config

from altools.client import HttpClient

userapi_cli = HttpClient(config.USER_API)
