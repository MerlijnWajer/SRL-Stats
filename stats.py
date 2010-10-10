#!/usr/bin/env python

from flup.server.fcgi import WSGIServer
from jinja2 import Template
from sql import *


def stats(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain;charset=utf8')])
#    tmpl = Template('Hello {{ name }}!')

#    route = env['PATH_INFO']
#    return [repr(route)]

#    return [str(tmpl.render({'name' : env['PATH_INFO']}))]
    return [repr(session.query(User).all())]
#    return [repr(env)]

if __name__ == '__main__':
    WSGIServer(stats).run()

