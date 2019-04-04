'''decos for vtools'''

import logging
from utils.excepts import ParamError

log = logging.getLogger()

def trans_col_to(column=''):
    '''对表做搜索需要转化其他字段为表字段

    设定value一定存在，根据rest的值和colu的值
    是否存在一共有4种情况
    rest,colu,解释
    y,n - 将转化后的值添加到原有的筛选
    y,y - 如果有相同的值(set&)，则取值，否则[-1]不存在
    n,y - 不存在
    n,n - 不存在

    '''
    def _(func):
        def wrapper(self, value):
            if not column:
                return func(self, value)
            # 如果value不存在(一般不会),则pass
            if not value:
                return None
            # 准备rest的值
            rest = func(self, value)
            if not rest:
                rest = []
            elif not isinstance(rest, list):
                rest = [rest]
            # 初始化values和准备colu的值
            if column not in self.values:
                self.values[column] = []
            elif not isinstance (self.values[column], list):
                self.values[column] = [self.values[column]]
            colu = self.values[column]
            # 判断
            if not rest:
                self.values[column] = [-1]
            else:
                if not colu:
                    colu.extend(rest)
                else:
                    ret = set(colu) & set(rest)
                    if ret:
                        self.values[column] = list(ret)
                    else:
                        self.values[column] = [-1]
            return rest
        return wrapper
    return _

def keep_thrift_conn(func):
    def __(self, *args, **kw):
        with self.keep_conn():
            ret = func(self, *args, **kw)
        return ret
    return __

def required(field=''):
    def _(func):
        def wrapper(self, value):
            _exist = (0, )
            if not value and value not in _exist:
                raise ParamError('缺少参数{}'.format(field))
            return func(self, value)
        return wrapper
    return _

def required_for(kw, method=None, field=''):
    def _(func):
        def wrapper(self, value):
            if not isinstance(kw, dict):
                log.warn('MH> {} is not dict type'.format(kw))
                raise ParamError('内部错误')
            method_result = True
            args_result = True
            if method is not None:
                if isinstance(method, (tuple, list)):
                    if self.method in method and (value is None or value == ''):
                        method_result = False
                elif self.method == method and (value is None or value == ''):
                    method_result = False
            for k,v in kw.items():
                if self.values.get(k) == v and (value is None or value == ''):
                    args_result = False
            if method_result is False or args_result is False:
                raise ParamError('参数{}未填写'.format(field))
            return func(self, value)
        return wrapper
    return _

def existence(func):
    def _(self, value):
        if value is None:
            return None
        return func(self, value)
    return _
