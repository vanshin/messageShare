#coding=utf-8

'''main'''

import os
import datetime

from altools.base.output import output

from flask import request, current_app
from sqlalchemy.orm import sessionmaker
from utils.constants import MesDef
from model.message import Message
from . import main

@main.route('/message', methods=['POST'])
def post_message():
    '''添加一个消息'''

    d = request.values
    content = d.get('content', '')
    mes_type = d.get('type', MesDef.MESS_TYPE_TEXT)
    own_user = '9181'
    descr = d.get('descr', '')
    attr = d.get('attr', '')

    now = datetime.datetime.now()

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

@main.route('/message', methods=['GET'])
def get_message():
    '''获取消息'''
    d = request.values
    mes_type = d.get('type', 1)
    limit = d.get('limit', 10)

    ret = {'messages': []}
    mes = current_app.dbsess.query(Message).order_by(Message.update_time)[0:10]
    for m in mes:
        tmp = {}
        tmp['content'] = m.content
        tmp['type'] = m.type
        tmp['attr'] = m.attr
        ret['messages'].append(tmp)
    return output(data=ret)


@main.route('/ping', methods=['GET'])
def get_ping():
    '''ping'''
    return output()
