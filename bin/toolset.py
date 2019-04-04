'''工具合集'''

import uuid
import string
import traceback
import config
import logging

from qfcommon3.server.client import ThriftClient
from qfcommon3.thriftclient.spring import Spring

from utils.excepts import ParamError

log = logging.getLogger()

LETTER_DIGIT = string.ascii_letters + string.digits



class ToolSet(object):

    @staticmethod
    def uuid():
        return uuid.uuid4().hex

    @staticmethod
    def to_list(data):
        ret = []
        if not isinstance(data, dict):
            raise ParamError('内部错误')
        for k,v in data.items():
            item = {}
            item['name'] = k
            item['value'] = v
            ret.append(item)
        return ret

    @staticmethod
    def utf8_rules(rules):
        '''仅限规则使用的转换utf8工具'''

        for rule in rules:
            if len(rule) != 3: continue
            for index, value in enumerate(rule):
                rule[index] = ToolSet.trans_to(rule[index], ToolSet.unicode_to_utf8)
        return rules


    @staticmethod
    def rebuild(items, key, value=None):
        '''重新组装为dict'''

        ret = {}
        if isinstance(items, list):
            for i in items:
                ret_key = i.get(key)
                if not ret_key:
                    continue
                ret_value = i.get(value) if value else i
                ret[ret_key] = ret_value
        return ret


    @staticmethod
    def getid():
        '''通过spring生成id'''
        return ThriftClient(config.SPRING_SERVERS, Spring).getid()

    @staticmethod
    def springid():
        '''通过spring生成id'''
        return ThriftClient(config.SPRING_SERVERS, Spring).getid()

    @staticmethod
    def trans_to(args, func):
        try:
            if isinstance(args, (list, set)):
                return list(map(func, args))
            if isinstance(args, (dict)):
                for k,v in args.items():
                    args[k] = func(v)
                return args
            return func(args)
        except:
            log.warn(traceback.format_exc())
            raise ParamError('转化失败')

    @staticmethod
    def str_len(name, cn=1, en=1):

        len_of_name = 0
        try:
            if isinstance(name, bytes):
                name = name.decode('utf8')
            for i in name:
                if i in LETTER_DIGIT:
                    len_of_name += en
                else:
                    len_of_name += cn
        except:
            log.warn(traceback.format_exc())
            return 0 # 字符串长度设置为0
        return len_of_name

    @staticmethod
    def just_letter_digit(v):
        if set(LETTER_DIGIT) & set(v) != set(v):
            return False
        return True

