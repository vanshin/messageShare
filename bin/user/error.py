#coding=utf8

'''error code'''

from . import user
from altools.base.output import output
from altools.base.error import ParamExcp, UserExcp

@user.errorhandler(ParamExcp)
def param_excp(e):
    return output(e.code, e.message)

@user.errorhandler(UserExcp)
def user_excp(e):
    return output(e.code, e.message)
