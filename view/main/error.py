#coding=utf8

'''error code'''

from . import main
from altools.base.output import output
from altools.base.error import ParamExcp, UserExcp

@main.errorhandler(ParamExcp)
def param_excp(e):
    return output(e.code, e.message)

@main.errorhandler(UserExcp)
def user_excp(e):
    return output(e.code, e.message)
