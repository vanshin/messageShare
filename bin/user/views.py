#coding=utf-8

'''user'''

import os
import datetime
import config
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

from altools.client import HttpClient
from altools.base.output import output
from altools.base.error import UserExcp

from flask import request, current_app
from sqlalchemy.orm import sessionmaker
from model.message import Message
from utils.constants import MesDef
from utils.runtime import userapi_cli
from . import user

@user.route('/login', methods=['POST'])
def post_login():
    '''登录'''

    d = request.values
    username = d.get('username')
    password = d.get('password')


    hc = httpClient(config.USER_API)
    ret = hc.get('login', {'usename': username, 'password': password})
    if not ret or ret['code'] != '0000':
        raise UserExcp('登录失败')
    return output(ret['data'])

@user.route('/regi', methods=['POST'])
def post_regi():
    '''注册'''

    ret = userapi_cli.post('user', request.values)
    log.debug(ret)
    if not ret or ret['code'] != '0000':
        raise UserExcp('注册失败')
    return output(ret['data'])
