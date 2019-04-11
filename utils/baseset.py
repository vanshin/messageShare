# coding=utf8

import traceback
import logging

from thrift.Thrift import TException
from qfcommon3.server.client import ThriftClient
from qfcommon3.thriftclient.apollo.ttypes import ApolloException

from utils.excepts import ThirdError, ServerError

log = logging.getLogger()

DEFAULT = 1
KEEP_CONN = 2

class BaseSet(object):

    def __init__(self, addr, thrift, framed=False):
        self.addr = addr
        self.thrift = thrift
        self.framed = framed
        # 各种模式
        self.long_conn = None
        self.mode = DEFAULT
        #
        self.other_thrift_conns = {
            'source': {
                'thrift': thrift,
                'addr': addr,
                'framed': framed
            }
        }

    def _thrift_name(self, thrift):
        return thrift.__name__.split('.')[-1]

    # 代理了apolloclient的调用
    def __getattr__(self, func_name):
        def _(*args, **kwargs):
            try:
                conn = self.get_conn()
                log.info('func={}|args={}'.format(func_name,(args, kwargs)))
                return conn.call(func_name, *args, **kwargs)
            except ApolloException as e:
                log.warn(traceback.format_exc())
                raise ThirdError('用户服务错误,{}'.format(e.respmsg))
            except TException as e:
                log.warn(traceback.format_exc())
                raise ThirdError('内部服务错误,{}'.format(e))
            except:
                log.warn(traceback.format_exc())
                raise ThirdError('内部错误')
        return _

    def keep_conn(self):
        log.info('keep thrift conn')
        self.mode = KEEP_CONN
        self.long_conn = self._create_thrift_conn()
        self._exit_func = self._keep_conn_exit
        return self

    def sw_conn(self, conn_name):
        if conn_name not in self.other_thrift_conns:
            raise ParamError('指定的thrift连接不存在')
        conn_dict = self.other_thrift_conns[conn_name]
        self.thrift = conn_dict['thrift']
        self.addr = conn_dict['addr']
        self.framed = conn_dict['framed']
        self._exit_func = self._sw_conn_exit

    def _sw_conn_exit(self):
        log.info('exit sw conn')
        source = self.other_thrift_conns['source']
        self.thrift = source['thrift']
        self.addr = source['addr']
        self.framed = source['framed']

    def _keep_conn_exit(self):
        log.info('exit conn keep')
        self.mode = DEFAULT
        self.long_conn = None

    def __str__(self):
        addr = ';'.join([f"{i['addr'][0]}:{i['addr'][1]}" for i in self.addr])
        thrift_name = self.thrift.__name__.split('.')[-1]
        return f'<{self.__class__.__name__} with {thrift_name} on {addr}>'

    def __enter__(self):
        self._use_with = True

    def __exit__(self, exc_type, exc_value, traceback):
        self._use_with = False
        self._exit_func()

    def _create_thrift_conn(self):
        try:
            thrift_cli = ThriftClient(
                self.addr, self.thrift, framed=self.framed, raise_except=True,
            )
        except:
            log.warn(traceback.format_exc())
            raise ThirdError('无法建立和服务的链接')
        return thrift_cli

    def get_conn(self):
        if self.mode == KEEP_CONN:
            if self._use_with == False:
                raise ServerError('请使用上下文管理来启用连接保持')
            return self.long_conn
        return self._create_thrift_conn()

    @classmethod
    def from_obj(cls, obj):
        return cls(obj.addr, obj.thrift)

    def register(self, thrift, addr, framed=False):
        self.other_thrift_conns[self._thrift_name(thrift)] = {
            'thrift': thrift,
            'addr': addr,
            'framed': framed
        }

