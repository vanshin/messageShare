'''main'''

import os
import logging
import json
import datetime
import hashids
import config
logging.basicConfig(filename=config.LOG_FILE, level=logging.DEBUG)
log = logging.getLogger()

from altools.base.output import output
from altools.base.error import ParamExcp
from altools.utils.tools import encode_id, decode_id

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

@main.route('/message', methods=['GET'])
@check_login()
def get_message():
    '''获取消息'''
    d = request.values
    mes_type = d.get('type', 1)
    length= d.get('length', 10)
    start = d.get('start', 1)
    attr = d.get('attr')

    userid = session.get('userid')
    log.debug('userid={}'.format(userid))

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
    kw['own_user'] = userid

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
        tmp['descr'] = m.descr
        tmp['id'] = encode_id(m.id)
        tmp['status'] = m.status
        ret['messages'].append(tmp)
    return output(data=ret)

@main.route('/message', methods=['PUT'])
@check_login()
def put_message():
    '''更新一个消息'''
    d = request.values
    mess_id = d.get('mid')
    if not mess_id:
        raise ParamExcp('缺乏messid')
    userid = session.get('userid')

    values = {'update_time': str(datetime.datetime.now())}
    for i in ['content', 'attr', 'type', 'status', 'descr']:
        value = d.get(i)
        if i == 'attr':
            value = json.loads(value)
        if value:
            values[i] = value

    mess_id = decode_id(mess_id)
    (current_app.dbsess.query(Message).filter_by(id=mess_id, own_user=userid)
        .update(values))
    current_app.dbsess.commit()
    return output()

@main.route('/ping', methods=['GET'])
def get_ping():
    '''ping'''
    return output()

from base.handler import BaseView

class Message(BaseView):

    async def get(self):

        self.args_idft = {
            'int': ['type']
        }

        v = self.build_args(dtype='json', dofor='page')


