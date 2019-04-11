'''
web api tools by vanshin

MisHandler:
    build_lists: 用于分页，包含数据和长度信息
    build_args: 参数的类型识别控制转化
    build_excel: 根据数据组织成excel
    is_excel: 根据mode参数判断是否是下载excel
VUtil:
    make_excel: 根据参数组织excel
(decos):
    trans_col_to: 配合build_args使用，将某个数据库的
        字段转化为另外一个字段

'''

import io
import copy
import logging
import openpyxl
import datetime
import traceback

from qfcommon3.base.dbpool import get_connection_exception

from utils.excepts import ParamError, BaseError, ServerError
from utils.base import BaseHandler
from utils.sets import MisInspector

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

log = logging.getLogger()

__version__ = '2.9.0'



class ArgsBuilder(object):
    '''用来识别，转化，控制参数'''

    # 如何build模式
    # 不同的模式对于参数的处理不一样
    # page用于分页
    _default_how = ('all', 'existence', 'page')
    _required_handler_info_key = ('method', )

    def __init__(self, args_idft=None, source=None, how="all", **kw):
        '''初始化'''

        # 实例化args lang map
        self.args_lang_map = getattr(self, 'args_lang_map', {})
        # 参数定义
        if not args_idft:
            log.warn('MH> no args_idft')
            raise ParamError('参数形式未定义')
        self.args_idft = args_idft
        self.all_args = []
        for k,v in self.args_idft.items():
            self.all_args.extend(v)
        # 原始参数
        self.source = source or {}
        # 经过检测以后的参数
        self.values = {}
        # 用来存放有values衍生出的参数
        self.others = {}
        # 控制如何验证参数
        if how not in self._default_how:
            log.warn('MH> unsupported how args({}): {}'.format(
                ','.join(self._default_how), how))
            raise ParamError('参数验证错误')
        self.how = how
        self.required_args = set()
        # 自动添加分页控制参数
        if self.how == 'page':
            if not 'int' in self.args_idft:
                self.args_idft['int'] = []
            self.args_idft['int'].extend(['page', 'size', 'offset'])
        # 控制业务逻辑校验方法执行顺序
        if not hasattr(self, 'check_order'):
            self.check_order = []
        # 参数验证检测类
        inspector_class = getattr(self, 'inspector_kls', MisInspector)
        log.info('MH> inspector == {}'.format(inspector_class.__name__))
        self.inspector = inspector_class()
        # 载入请求的相关信息
        for key in self._required_handler_info_key:
            if key not in kw:
                log.warn('MH> need reqired handler info {}'.format(key))
                raise ParamError('内部错误')
            setattr(self, key, kw[key])

    def _page_type_detection(self, arg_name):

        # 自动添加时间的区间
        if arg_name.endswith('time'):
            times = arg_name+'_stime'
            timee = arg_name+'_etime'
            if times in self.source and timee in self.source:
                if not 'datetime' in self.args_idft:
                    self.args_idft['datetime'] = []
                self.args_idft['datetime'].append(times)
                self.args_idft['datetime'].append(timee)

        # 自动添加日期的区间
        if arg_name.endswith('date'):
            dates = arg_name+'_sdate'
            datee = arg_name+'_edate'
            if dates in self.source and datee in self.source:
                if not 'date' in self.args_idft:
                    self.args_idft['date'] = []
                self.args_idft['date'].append(dates)
                self.args_idft['date'].append(datee)

    def _type_detection(self):
        '''类型校验

        功能:
            按照模式判断参数是否存在
            判断参数是否符合类型
            自动解析参数为指定类型并存储在values
        其他:
            被认为是空的数据不会被添加到values里面

        '''

        # 添加在page模式下处理一些逻辑
        for i in self.all_args:
            if self.how == 'page':
                self._page_type_detection(i)

        # 是否存在校验、类型校验
        for arg_type, arg_name_list in self.args_idft.items():
            for arg_name in arg_name_list:
                value = self._check_trans_type(arg_type, arg_name)
                # all 模式  none在之前就报错了
                # exist 模式 none是不存在的数据，从这里过滤
                # page 模式 none 同上
                if value is not None:
                    self.values[arg_name] = value

    def _logic_detection(self):
        '''业务逻辑校验

        功能:
            指定调用业务逻辑函数顺序
            调用每个字段的业务逻辑函数
        其他:
            被认为是空的数据不会被添加到values里面

        '''

        # 业务逻辑校验(顺序)
        notin_order = set(self.all_args) - set(self.check_order)
        all_check_order = self.check_order + list(notin_order)
        for k in all_check_order:
            v = self.values.get(k)
            bl_verify_func = getattr(self, k, self._default)
            ret = bl_verify_func(v)
            if self.how in ('existence', 'page') and ret is None:
                if k in self.values:
                    self.values.pop(k)
                continue
            self.values[k] = ret

    def is_valid_value(self, inspected_ret):
        '''判断验证后的值是否是有效可用的值'''
        if inspected_ret is None or inspected_ret == '':
            return False
        return True

    def _check_trans_type(self, arg_type, arg_key):
        ''' 类型校验和转化

        params:
            arg_type: 参数类型
            arg_key: 取参数键
        return:
            inspected_ret: 经过校验函数处理以后的值

        '''
        arg_value = self.source.get(arg_key)

        # 加载错误信息
        zh_arg_name = self.args_lang_map.get(arg_key) or arg_key
        not_exist_err = '{}未填写'.format(zh_arg_name)
        arg_type_err = '{}格式错误'.format(zh_arg_name)

        # 确保检测类存在检测函数
        inspector_func = getattr(self.inspector, 'v_'+arg_type, None)
        if not inspector_func:
            log.warn('MH> unsupport type checker {} for {}'.format(
                arg_type, arg_key))
            raise ParamError('系统内部错误')

        # 使用检测类检测转化参数
        try:
            inspected_ret = inspector_func(arg_value)
        except BaseError as e:
            log.warn('MH> inspector func raise except')
            raise ParamError(e.errmsg)
        except:
            log.warn('MH> other except: \n {}'.format(traceback.format_exc()))
            raise ServerError('系统内部错误')

        if inspected_ret is False:
            log.warn('MH> args type error {}:{}-> {}'.format(
                arg_type, arg_key, arg_value))
            raise ParamError(arg_type_err)
        # all 和 existence的必填的参数
        if self.how == 'all':
            if not self.is_valid_value(inspected_ret):
                log.warn('MH> {} is required, now is {}'.format(
                    arg_key, inspected_ret))
                raise ParamError(not_exist_err)
        if self.how == 'existence':
            if arg_key in self.required_args and not self.is_valid_value(inspected_ret):
                log.warn('MH> {} is required, now is {}'.format(
                    arg_key, inspected_ret))
                raise ParamError(not_exist_err)
        # page 模式自动去除未填写的搜索框
        if self.how == 'page':
            if arg_value == '':
                inspected_ret = None
            if arg_key == 'page' and not inspected_ret:
                inspected_ret = 0
            if arg_key == 'size' and not inspected_ret:
                inspected_ret = 10


        return inspected_ret

    def _default(self, value):
        return value

    def set_required_args(self, args):
        if not isinstance(args, (set, list, tuple)):
            raise ParamError('不是指定的数据类型')
        args = set(args)
        self.required_args |= args

    def build(self):
        '''参数生成'''
        log.debug(self.required_args)

        self._type_detection()
        self._logic_detection()

class ListBuilder(object):

    _how = ('page', 'list')
    attr_op_map = {
        'ge': '>=',
        'gt': '>',
        'lt': '<',
        'le': '<=',
    }

    def __init__(self, source, fields, rules, limits):
        self.db, self.table = source.split('.')
        self.fields = fields
        self.rules = rules
        self.limits = limits
        self._limit_to_other()

    @classmethod
    def from_list_args(cls, list_args):
        if 'source' not in list_args:
            raise ParamError('没有来源')
        fields = list_args.get('fields') or '*'
        rules = list_args.get('rules') or []
        limits = list_args.get('limits') or {}
        return cls(list_args['source'], fields, rules, limits)

    def _limit_to_other(self):

        self.group_by = ''
        self.order_by = ''
        self.sort = ''
        for limit_name, limit_value in self.limits.items():
            if limit_name == 'group_by':
                self.group_by = 'group by {}'.format(limit_value)
            if limit_name == 'order_by':
                self.order_by = 'order by {}'.format(limit_value)
            if limit_name == 'sort':
                self.sort = limit_value
        self.other_total = '{} {} {}'.format(self.group_by, self.order_by, self.sort)
        self.other = self.other_total + ' limit {} offset {}'

    def w_key(self, key):
        '''包裹key用``'''
        return '`{}`'.format(key)

    def _value_by_rule_from_data(self, rule, data):
        '''从数据里面取值'''

        value = data.get(rule)
        if value is None:
            if rule.endswith('time'):
                # 兼容以前版本默认是start_time的情况
                start_time = data.get('start_time')
                end_time = data.get('end_time')
                # ctime_stime ctime_etime
                start_time = data.get(f'{rule}_stime') or start_time
                end_time = data.get(f'{rule}_etime') or end_time
                if start_time and end_time:
                    value = (start_time, end_time)
            elif rule.endswith('date'):
                start_date = data.get(f'{rule}_sdate')
                end_date = data.get(f'{rule}_edate')
                if start_date and end_date:
                    value = (start_date, end_date)
        return value

    def _parse_rule(self, rule):
        '''解析带控制属性(fuzzy.nickname)的rule'''

        attr = None
        if '.' in rule:
            attr, rule = rule.split('.')
        return attr, rule

    def _rule_to_where(self, data):
        '''根据rule和value的值自动设置where'''

        self.where = {}

        for rule in self.rules:
            attr, rule = self._parse_rule(rule)
            value = self._value_by_rule_from_data(rule, data)
            # 过滤掉数据为空
            if value is None:
                continue
            # 根据属性去定义where的类型
            # 默认属性(无属性)
            if attr is None:
                if isinstance(value ,list):
                    self.where[rule] = ('in', value)
                else:
                    self.where[rule] = value
            elif attr == 'fuzzy':
                self.where[rule] = ('like', f'%{value}%')
            elif attr == 'timein':
                self.where[rule] = ('between', value)
            elif attr == 'lfuzzy':
                self.where[rule] = ('like', f'%{value}')
            elif attr == 'rfuzzy':
                self.where[rule] = ('like', f'{value}%')
            # 其他区间使用gt/lt模拟
            # 时间区间特别处理(用的多)
            elif attr in self.attr_op_map:
                self.where[rule] = (self.attr_op_map[attr], value)

        # 处理other,加上limit offset
        self.offset = data.get('offset') or data['page'] * data['size']
        self.limit = data['size']
        self.other = self.other.format(self.limit, self.offset)


    def _limit_to_where(self):

        for limit_name, limit_value in self.limits.items():
            if not limit_value:
                continue
            if limit_name in ('group_by', 'order_by', 'sort'):
                continue
            if isinstance(limit_value, tuple):
                if len(limit_value) != 2:
                    log.warn('MH> limits setting error {}'.format(limit_value))
                    continue
                value = limit_value[1]
                # ('in', []) 去除这种以及类似情况
                # FIXME
                if not value and value not in (0, ):
                    continue

            if limit_name in self.where:
                limit_name = self.w_key(limit_name)
            self.where[limit_name] = limit_value

    def _query_list(self, how='page'):

        lists = []
        try:
            with get_connection_exception(self.db) as db:
                lists = db.select(
                    table = self.table,
                    fields = self.fields,
                    where = self.where,
                    other = self.other if how == 'page' else self.other_total
                ) or []
        except:
            log.warn(traceback.format_exc())
            raise ParamError('查询数据失败')
        self.lists = lists
        return self.lists

    def _query_count(self):
        total = []
        try:
            with get_connection_exception(self.db) as db:
                total = db.select(
                    table = self.table,
                    fields = 'count(*) as total',
                    where = self.where,
                    other = self.other_total
                ) or []
        except:
            log.warn(traceback.format_exc())
            raise ParamError('查询数据失败')
        self.total = len(total) if self.group_by else total[0]['total']
        return self.total

    def build(self, data, how):

        data = {'page': 0, 'size': 10} if data is None else data

        self._rule_to_where(data)
        log.debug(self.where)
        self._limit_to_where()

        if how == 'page':
            self.ret = {'list': [], 'total': 0}
            self.ret['list'] = self._query_list(how)
            self.ret['total'] = self._query_count()
        elif how == 'list':
            self.ret = self._query_list(how)
        return self.ret

class MisHandler(BaseHandler):

    _dofors = ('all', 'existence', 'page')
    _dtype = ('form', 'json')

    def initial(self):
        BaseHandler.initial(self)

        self.args_builder = getattr(self, 'args_builder', ArgsBuilder)
        self.args_idft= {}
        self.args_lang_map = {}
        self.required_args = set()
        self.method = self.req.method.lower()

        # 代理了initial
        if hasattr(self, 'before_api_call'):
            self.before_api_call()

    def finish(self):

        # 代理了finish
        if hasattr(self, 'after_api_call'):
            self.after_api_call()

    def _perm_proxy(self):
        '''代理权限设置

        代理_perm_codes = [('get', 'xxxx'), ('post', 'xxxx')]情况

        '''

        if not hasattr(self, '_perm_codes'):
            return
        if not isinstance(self._perm_codes, (tuple, list)):
            return
        for i in self._perm_codes:
            # ('get', 'xxxx')
            if isinstance(i, tuple) and len(i) == 2:
                method = str(i[0]).upper()
                code = str(i[1])
                if method not in ('get', 'post', 'put'):
                    raise ServerError('非法的权限对应方法')
                if method != self.method:
                    continue
                self._perm_codes = code

    def source_by_dtype(self, dtype):
        '''获取初始数据'''

        if hasattr(self, 'source_data'):
            return self.source_data

        # 不要污染原数据,支持json
        source_data = {}
        if dtype == 'form':
            source_data = self.req.input()
        elif dtype == 'json':
            source_data = self.req.inputjson()
        self.source_data = copy.deepcopy(source_data)
        return self.source_data

    def build_args(self, dtype='form', dofor='all'):
        '''验证参数

        params:
            dtype(str): 如何获取前端的数据 (json, form)
            dofor(str): 如何生成参数 (all, existence, ……)
        return:
            args: 返回指定类型的参数

        all:
            验证所有的参数(除了manual)符合指定类型并且存在, 默认模式
        existence:
            验证存在的参数,符合指定类型. 用在分页查询等接口
        page:
            分页数据，自动从参数中寻找分页控制参数

        '''

        if dofor not in self._dofors:
            log.warn('MH> not support dofor {}'.format(dofor))
            raise ParamError('内部错误')
        if dtype not in self._dtype:
            log.warn('MH> not support dtype {}'.format(dtype))
            raise ParamError('内部错误')

        if hasattr(self, 'values') and self.values:
            return self.values

        log.info('MH> args_builder == {}'.format(self.args_builder.__name__))

        # 初始化数据
        self.source_by_dtype(dtype)
        # 生成args builder实例并执行build
        self._aber= self.args_builder(
            self.args_idft, self.source_data, dofor,
            method=self.method,
        )
        if self.required_args:
            self._aber.set_required_args(self.required_args)
        self._aber.build()

        # 生成的数据
        self.values = self._aber.values
        self.others = self._aber.others
        self.source = self._aber.source
        log.info('MH> built_source == {}'.format(self.source))
        log.info('MH> built_args == {}'.format(self.values))
        log.info('MH> built_others == {}'.format(self.others))
        return self.values

    def require(self, *args):
        for arg in args:
            self.required_args.add(arg)

    def build_new_lists(self, data=None, dofor='page'):
        '''从哪个地方根据什么规则获取什么数据'''

        self._list_builder = ListBuilder
        self._lber = self._list_builder.from_list_args(self.list_args)
        ret = self._lber.build(data, dofor)
        return ret

    def build_excel(self, head, data, name='数据.xlsx'):
        if not head:
            raise ParamError('缺少excel列表头部')

        self.set_headers({'Content-Type': 'application/octet-stream'})
        self.set_headers(
            {'Content-disposition': 'attachment; filename={}'.format(name)})

        return VUtil.make_excel(head, data, name)

    def is_expo_excel(self):
        if self.req.input().get('mode') == 'expo_excel':
            return True
        return False

class VUtil(object):

    @staticmethod
    def make_excel(head, data, name):
        '''根据head组织data形成excel数据
        params:
            head(list<str>): ['商户id', '渠道id', ……]
            data(list<list>: [[11327, ……], [11751, ……], ……]
        return:
            stream
        '''

        workbook = openpyxl.Workbook()
        worksheet = workbook.active

        worksheet.append(head)
        for rows in data:
            worksheet.append(rows)
        bio = io.BytesIO()
        workbook.save(bio)
        return bio.getvalue()

