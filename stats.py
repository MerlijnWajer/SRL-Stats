#!/usr/bin/env python

# Routes:
# /graph for graphs? (filetype png?)
# /user etc for user pages? etc

from flup.server.fcgi import WSGIServer
from jinja2 import Environment, PackageLoader
from sql import *
from webtool import WebTool


def stats(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html;charset=utf8')])

    return [wt.apply_rule(env['REQUEST_URI'])]

def general():
    users = session.query(User).limit(10)
    scripts = session.query(Script).limit(10)

    tmpl = jinjaenv.get_template('main.html')
    return str(tmpl.render({'users' : users, 'scripts' : scripts}))

def user(userid):
    return general()

def graph(graphvar):
    return repr(graphvar)

if __name__ == '__main__':
    jinjaenv = Environment(loader=PackageLoader('stats', 'templates'))
    wt = WebTool()

    import re
    wt.add_rule(re.compile('/stats/user/([0-9]+)'), user, ['userid'])
    wt.add_rule(re.compile('/stats/graph/(.+)'), graph, ['graphvar'])
    wt.add_rule(re.compile('/stats'), general, [])
    WSGIServer(stats).run()

