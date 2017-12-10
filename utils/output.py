#coding=utf-8
import json
import datetime
import config

from flask import jsonify
from flask import request

def json_default_trans(obj):
    '''json对处理不了的格式的处理方法'''
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError('%r is not JSON serializable' % obj)



def output(code=0000, message='success', data=None):
    ret = {
        'code': code,
        'mess': message,
        'data': {}
    }
    if not data:
        return jsonify(ret)
    ret['data'] = data

    return jsonify(ret)

