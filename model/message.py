#coding=utf-8

import sys
import os
import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UnicodeText, DateTime, JSON

Base = declarative_base()

class Message(Base):
    '''messages'''

    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    type = Column(Integer)
    content = Column(UnicodeText)
    shared_user = Column(Integer)
    own_user = Column(Integer)
    status = Column(Integer)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    descr = Column(UnicodeText)
    attr = Column(JSON)


