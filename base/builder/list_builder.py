'''列表建造者'''

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
