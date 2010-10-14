#!/usr/bin/env python

# TODO:
# Fix templates so not every child has to get data for the ``total'' stats
# as well.

# Routes:
# /graph for graphs? (filetype png?)
# /script for script pages
# /user for user pages ex: /user/42/ or /user/script or user/commits
# /var for var pages ex: /var/42
# /commit/:commitid specific commit info

from flup.server.fcgi import WSGIServer
from jinja2 import Environment, PackageLoader
from sql import *
from webtool import WebTool

# Import UserTool
from query import UserTool, ScriptTool

BASE_URL = '/stats'

# URLs:
"""
/user/:id           |   User Info (Total Commits, etc) Owned Scripts
/user/:id/commits   |   User Commits

/script/:id         |   Script Info (Total Vars/Commits)
/script/:id/commits |   Commits made to script. (list last X)

/commit/:id         |   Commit Info (Vars, time, user, script)
/commit/all         |   Commit List.
"""

def stats(env, start_response):
    r = wt.apply_rule(env['REQUEST_URI'])
    if r is None:
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        r = '404: %s' % env['REQUEST_URI']
    else:
        start_response('200 OK', [('Content-Type', 'text/html;charset=utf8')])

    return [r]

def general():
    tmpl = jinjaenv.get_template('base.html')

    return str(tmpl.render({'users' : ut.top(5), 'scripts' : st.top(5)}))


def user(userid=None):
    tmpl = jinjaenv.get_template('user.html')
    uinfo = ut.info(userid)

    return str(tmpl.render(
        {   'users' : ut.top(5), 'scripts' : st.top(5),
            'ttc' : uinfo['time'][1],
            'tc' : uinfo['time'][0], 'user' : uinfo['user']}
        ))

def user_commit(userid=None):
    tmpl = jinjaenv.get_template('usercommits.html')
    user = session.query(User).filter(User.id==userid).first()

    return str(tmpl.render(
        {   'users' : ut.top(5), 'scripts' : st.top(5),
            'user' : user, 'commits' : ut.list(user)}
        ))

def script(scriptid=None):
    tmpl = jinjaenv.get_template('script.html')
    sinfo = st.info(scriptid)

    return str(tmpl.render(
        {   'users' : ut.top(5), 'scripts' : st.top(5),
            'ttc' : sinfo['time'][1], 'tc' : sinfo['time'][0],
            'script' : sinfo['script'], 'vars' : sinfo['vars']}
        ))

def script_commit(scriptid=None):
    tmpl = jinjaenv.get_template('scriptcommits.html')
    script = session.query(Script).filter(Script.id==scriptid).first()

    return str(tmpl.render(
        {   'users' : ut.top(5), 'scripts' : st.top(5),
            'script' : script, 'commits' : st.list(script)}
        ))

if __name__ == '__main__':
    jinjaenv = Environment(loader=PackageLoader('stats', 'templates'))
    wt = WebTool()
    ut = UserTool(session)
    st = ScriptTool(session)

    import re

    # XXX: TODO: Integers hard limited at 6 chars max. Python has unlimited
    # integers; but databases do not. If someone passes 999999999999999999
    # then we will get a database error. This ``fix'' works around it.
    # Until you get more than 999999 users.
    wt.add_rule(re.compile('^%s/user/([0-9]{1,6})/?$' % BASE_URL),
            user, ['userid'])

    wt.add_rule(re.compile('^%s/user/([0-9]{1,6})/commits/?$' % BASE_URL),
            user_commit, ['userid'])

    wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/?$' % BASE_URL),
            script, ['scriptid'])

    wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/commits/?$' % BASE_URL),
            script_commit, ['scriptid'])

    wt.add_rule(re.compile('^%s/?$' % BASE_URL),
                general, [])

    WSGIServer(stats).run()

