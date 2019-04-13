from aiopeewee import AioModel, AioMySQLDatabase

from peewee import CharField, IntegerField

db_blog = AioMySQLDatabase('blog', user='op_blog', password='blog_126ac9f6')

class article(AioModel):

    id = IntegerField(primary_key=True)
    userid = IntegerField()
    title = CharField(max_length=64)
    body = CharField(max_length=2048)

    class Meta:
        database = db_blog
