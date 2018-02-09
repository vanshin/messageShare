#coding=utf8

'''deco func'''

import time

from session import LoginUser

def check_login(session_id):
    def __(func):
        def _(*args, **kwargs):

