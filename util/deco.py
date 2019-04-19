#coding=utf8

'''deco func'''

import time
import logging
import flask
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

from functools import wraps

from altools.base.error import UserExcp
from utils.constants import UserConst
from .runtime import userapi_cli

def check_login():
    def __(func):
        @wraps(func)
        def _(*args, **kwargs):
            cookies = flask.request.cookies
            log.info('dfdfdfdf')
            req_data = {'session_id': cookies.get('session_id')}
            log.info('session={}'.format(req_data))
            info = userapi_cli.get('info', req_data)
            if not info or info['code'] != '0000':
                raise UserExcp('检查用户登录信息失败')
            data = info['data']
            if data.get('status') != UserConst.LOGGED:
                raise UserExcp('用户未登录-{}-'.format(data.get('status')))
            for k,v in data.items():
                flask.session[k] = v
            return func(*args, **kwargs)
        return _
    return __

