#coding=utf8

DATABASE_ENGINE = '{}://{}@{}:{}'

DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

class MesDef:

    # 消息类型
    MESS_TYPE_TEXT = 1000 # 普通文字
    MESS_TYPE_TEXT_ENCRY= 1110 # 文字加密

    MESS_TYPE_FILE = 2000 # 文件
    MESS_TYPE_FILE_PDF = 2100 # 文件pdf

    MESS_TYPE_MUTILMEDIA = 3000 # 多媒体


