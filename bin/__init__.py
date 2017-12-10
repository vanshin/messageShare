#coding=utf-8

from flask import Flask

def create_app(config_name):
    app = Flask(__name__)

    # 初始化组件

    # 蓝图

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
