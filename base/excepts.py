class BaseError(Exception):

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class ParamError(BaseError):

    def __init__(self, msg='参数错误'):
        BaseError.__init__(self, '4001', msg)
        self.msg = msg

class ServerError(BaseError):

    def __init__(self, msg='服务错误'):
        BaseError.__init__(self, '4002', msg)
        self.msg = msg


