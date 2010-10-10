#!/usr/bin/env python

from flup.server.fcgi import WSGIServer
from jinja2 import Template
from sql import *


def stats(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html;charset=utf8')])
    tmpl = Template('''<html><head></head><body>
            <ul>
            {% for user in users %}
                <li> {{ user }} </li>
            {% endfor %}
            </ul>
            </body>
            </html>''')

#    route = env['PATH_INFO']
#    return [repr(route)]

#    return [repr(session.query(User).all())]
    users = session.query(User).all()
    return [str(tmpl.render({'users' : users}))]
#    return [repr(env)]

if __name__ == '__main__':
    WSGIServer(stats).run()

