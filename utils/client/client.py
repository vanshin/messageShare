#coding=utf8

'''客户端'''

import os
import click


from requests import post

class config:
    test = {
        'host': '127.0.0.1',
        'port': '9181',
        'url': 'http://127.0.0.1:5000/message'
    }
    server = {
        'host': '127.0.0.1',
        'port': '9181',
    }
    env = {
        'test': test,
        'server': server
    }

@click.command()
@click.option('--content', type=click.STRING, help='填写消息内容', prompt='内容')
@click.option('--type', type=click.INT, help='消息类型(1-文字消息)', prompt='类型')
def upload(content, type):
    data = {
        'content': content,
        'type': type,
    }
    post(config.env['test'].get('url'), data=data)

if __name__ == '__main__':
    upload()
