#coding=utf-8

'''user'''

import os
import datetime

from flask import request, current_app
from sqlalchemy.orm import sessionmaker
from utils.constants import MesDef
from utils.output import output
from model.message import Message
from . import main

@user.route('/login', methods=['POST'])
def post_login():
    '''登录'''

    # check user pass

    # set session

    # login success

