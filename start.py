from quart import Quart
from urls import urls

app = Quart(__name__)

blues = []

for url, view_class in urls:
    func = getattr(view_class, 'as_view')
    blue = getattr(view_class, 'blue', None)

    if blue:
        blues.append(blue)
        blue.add_url_rule(url, view_func=func(view_class.__name__))
    else:
        app.add_url_rule(url, view_func=func(view_class.__name__))
for i in blues:
    app.register_blueprint(i)


if __name__ == '__main__':
    app.run()
