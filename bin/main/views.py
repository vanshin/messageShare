#coding=utf-8

'''main'''

import os
import datetime

from flask import request, current_app
from sqlalchemy.orm import sessionmaker
from utils.constants import MesDef
from utils.output import output
from model.message import Message
from . import main

@main.route('/message', methods=['POST'])
def post_message():
    '''添加一个消息'''

    d = request.values
    content = d.get('content', '')
    mes_type = d.get('type', MesDef.MESS_TYPE_TEXT)
    own_user = '9181'

    now = datetime.datetime.now()

    # insert
    message = Message(
        type=mes_type,
        content=content,
        status=1,
        own_user=own_user,
        create_time=now,
        update_time=now,
    )

    current_app.dbsess.add(message)
    current_app.dbsess.commit()

    return output()

@main.route('/ping', methods=['GET'])
def get_ping():
    '''ping'''
    return output()
