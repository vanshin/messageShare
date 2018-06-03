#coding=utf-8

'''main'''

import os
import logging
import json
import datetime
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

from altools.base.output import output
from altools.base.error import ParamExcp

from flask import request, current_app, session
from sqlalchemy.orm import sessionmaker
from utils.constants import MesDef
from utils.deco import check_login
from model.message import Message
from . import main

@main.route('/message', methods=['POST'])
@check_login()
def post_message():
    '''添加一个消息'''

    d = request.values
    content = d.get('content', '')
    mes_type = d.get('type', MesDef.MESS_TYPE_TEXT)
    descr = d.get('descr', '')
    attr = d.get('attr', '')
    now = datetime.datetime.now()
    log.info(session.get('userid'))

    own_user = session.get('userid')

    log.info('attr={}'.format(attr))

    try:
        attr = json.loads(attr)
    except:
        attr = ''

    # insert
    message = Message(
        type=mes_type,
        content=content,
        status=1,
        descr=descr,
        attr=attr,
        own_user=own_user,
        create_time=now,
        update_time=now,
    )

    current_app.dbsess.add(message)
    current_app.dbsess.commit()

    return output()

@check_login()
@main.route('/message', methods=['GET'])
def get_message():
    '''获取消息'''
    d = request.values
    mes_type = d.get('type', 1)
    length= d.get('length', 10)
    start = d.get('start', 1)
    attr = d.get('attr')

    try:
        if attr:
            attr = json.loads(attr)
    except:
        attr = {}

    if start < 1:
        raise ParamExcp('start page must gt 1')
    start = start - 1

    offset = start * length

    kw = {}
    kw['type'] = mes_type

    ret = {'messages': []}
    mes_query = (current_app
            .dbsess.query(Message)
            .filter_by(**kw))

    for k,v in attr.items():
        mes_query = mes_query.filter(Message.attr[k]==v)

    mes = (mes_query
        .order_by(Message.update_time.desc())
        .limit(length)
        .offset(offset))

    for m in mes:
        log.info('time={}'.format(m.create_time))
        tmp = {}
        tmp['content'] = m.content
        tmp['type'] = m.type
        tmp['attr'] = m.attr
        tmp['create_time'] = str(m.create_time)
        tmp['update_time'] = str(m.update_time)
        ret['messages'].append(tmp)
    return output(data=ret)


@main.route('/ping', methods=['GET'])
def get_ping():
    '''ping'''
    return output()
