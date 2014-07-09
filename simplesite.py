import cgi
from functools import wraps

TITLE = 'Untitled site'
MENU = [('Home', '/')]

def _get_menu(active_path):
    html = ''
    for title, path in MENU:
        data = dict(
            active=' class="active"' if active_path == path else '',
            path=cgi.escape(path),
            title=cgi.escape(title))
        html += '<li%(active)s><a href="%(path)s">%(title)s</a></li>' % data
    return html

def page(title):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            values = func(self, *args, **kwargs)
            if isinstance(values, basestring):
                values = dict(content=values)
            values.setdefault('title', title)

            self.response.write(
                '<!DOCTYPE html>'
                '<html>'
                '<head>'
                '<title>%(title)s</title>'
                '<link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">'
                '</head>'
                '<body>'
                '<div class="container">'
                '<div class="header">'
                '<ul class="nav nav-pills pull-right">%(menu)s</ul>'
                '<h3 class="text-muted">%(title)s</h3>'
                '</div>'
                '<h1>%(page_title)s</h1>' % dict(title=cgi.escape(TITLE),
                                                 page_title=cgi.escape(values['title']),
                                                 menu=_get_menu(self.request.path)))

            message = values.get('message')
            message_level = values.get('message_level', 'info')
            message_title = values.get('message_title')

            if message:
                if not message_title:
                    if message_level == 'danger':
                        message_title = 'Error'
                    elif message_level == 'warning':
                        message_title = 'Warning'
                    else:
                        message_title = 'Info'

                if isinstance(message, list):
                    message_html = '<br>'.join(map(message, cgi.escape))
                else:
                    message_html = cgi.escape(message)

                self.response.write(
                    '<div class="panel panel-%(level)s">'
                    '<div class="panel-heading">'
                    '<h3 class="panel-title">%(title)s</h3>'
                    '</div>'
                    '<div class="panel-body">%(message)s</div>'
                    '</div>' % dict(level=cgi.escape(message_level),
                                    title=cgi.escape(message_title),
                                    message=message_html))

            content = values.get('content')
            if content:
                self.response.write(content)

            self.response.write(
                '</div>'
                '</body>'
                '</html>')
        return wrapper

    # In case the decorator was called without parentheses.
    if callable(title):
        func = title
        title = 'Untitled'
        return decorator(func)

    return decorator
