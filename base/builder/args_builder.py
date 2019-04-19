'''参数建造者'''

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
            # log.warn('MH> no args_idft')
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
            # log.warn('MH> unsupported how args({}): {}'.format(
                # ','.join(self._default_how), how))
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
        # log.info('MH> inspector == {}'.format(inspector_class.__name__))
        self.inspector = inspector_class()
        # 载入请求的相关信息
        # for key in self._required_handler_info_key:
            # if key not in kw:
                # # log.warn('MH> need reqired handler info {}'.format(key))
                # raise ParamError('内部错误')
            # setattr(self, key, kw[key])

    async def _page_type_detection(self, arg_name):

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
            # log.warn('MH> unsupport type checker {} for {}'.format(
                # arg_type, arg_key))
            raise ParamError('系统内部错误')

        # 使用检测类检测转化参数
        try:
            inspected_ret = inspector_func(arg_value)
        except BaseError as e:
            # log.warn('MH> inspector func raise except')
            raise ParamError(e.errmsg)
        except:
            # log.warn('MH> other except: \n {}'.format(traceback.format_exc()))
            raise ServerError('系统内部错误')

        if inspected_ret is False:
            # log.warn('MH> args type error {}:{}-> {}'.format(
                # arg_type, arg_key, arg_value))
            raise ParamError(arg_type_err)
        # all 和 existence的必填的参数
        if self.how == 'all':
            if not self.is_valid_value(inspected_ret):
                # log.warn('MH> {} is required, now is {}'.format(
                    # arg_key, inspected_ret))
                raise ParamError(not_exist_err)
        if self.how == 'existence':
            if arg_key in self.required_args and not self.is_valid_value(inspected_ret):
                # log.warn('MH> {} is required, now is {}'.format(
                    # arg_key, inspected_ret))
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
        # log.debug(self.required_args)

        self._type_detection()
        self._logic_detection()

