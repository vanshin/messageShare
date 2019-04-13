
from base.handler import BaseView

from model.article import article
from model.article import db_blog

class Article(BaseView):

    async def get(self):

        self.args_idft = {
            'str': ['test']
        }

        v = await self.build_args()

        return 'test'

    async def post(self):
        await db_blog.connect()
        a = await article.create(id=125, title='test', body='kkkk', userid='123421')
        return 'kk'





