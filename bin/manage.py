#coding=utf-8

import sys
import os
HOME = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(HOME), 'conf'))
sys.path.append(os.path.join(os.path.dirname(HOME), 'model'))
sys.path.append(os.path.join(os.path.dirname(HOME), 'altools'))
sys.path.append(os.path.dirname(HOME))

import click
import sqlalchemy

from flask import current_app
from sqlalchemy.orm import sessionmaker
from bin import create_app
from config import dbconf

app = create_app('default')

def make_shell_context():
    """ 设置上下文 """
    pass


engine = sqlalchemy.create_engine(dbconf, echo=False)
Session = sessionmaker(bind=engine)
dbsess = Session()
with app.app_context():
    current_app.dbsess = dbsess

if __name__ == '__main__':
    app.run()

