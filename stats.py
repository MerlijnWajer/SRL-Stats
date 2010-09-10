#!/usr/bin/env python

from flup.server.fcgi import WSGIServer
from jinja2 import Template


def wsgi(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain;charset=utf8')])
#    return ["Ohai world"]
    tmpl = Template('Hello {{ name }}!')

    return [str(tmpl.render({'name' : env['PATH_INFO']}))]

if __name__ == '__main__':
    WSGIServer(wsgi).run()

