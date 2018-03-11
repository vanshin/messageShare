#coding=utf8

'''deco func'''

import time
import flask

from .runtime import userapi_cli
from .altools.base.error import UserExcp

def check_login(session_id):
    def __(func):
        def _(*args, **kwargs):
            req_data = {'session_id', session_id}
            info = userapi_cli.get('info', req_data)
            if not info or info['code'] != '0000':
                raise UserExcp('检查用户登录信息失败')
            data = info['data']
            if data.get('status') != UserConst.LOGGED:
                raise UserExcp('用户未登录-{}-'.format(data.get('status')))
            for k,v in data:
                flask.session[k] = v
            return func(*args, **kwargs)
        return _
    return __

