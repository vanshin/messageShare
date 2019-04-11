
from base.handler import BaseView

class Article(BaseView):

    async def get(self):

        self.args_idft = {
            'str': ['test']
        }

        v = await self.build_args()

        return 'test'




