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

# HAX.
import os
os.environ['MPLCONFIGDIR'] = '/tmp'

from flup.server.fcgi import WSGIServer
from jinja2 import Environment, PackageLoader
from sql import *
from webtool import WebTool

# Import UserTool
from query import UserTool, ScriptTool
from graph import GraphTool

BASE_URL = '/stats'
RESULTS_PER_PAGE = 25

def get_pageid(pageid):
    try:
        return max(int(pageid), 1)
    except (ValueError, TypeError):
        return 1


# URLs:
"""
/user/:id           |   User Info (Total Commits, etc) Owned Scripts
/user/:id/commits   |   User Commits
/user/:id/scripts   |   All scripts user committed to
/user/all/(:pageid) |   All users. (With possible pid)

/script/:id         |   Script Info (Total Vars/Commits)
/script/:id/commits |   Commits made to script. (list last X)
/script/:id/users   |   Users who committed to script. w/ total time
/script/all/(:pid)  |   All users. (With possible pid)

/commit/:id         |   Commit Info (Vars, time, user, script)
/commit/all         |   Commit List.
"""

def stats(env, start_response):
    r = wt.apply_rule(env['REQUEST_URI'])
    if r is None:
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        r = '404: %s' % env['REQUEST_URI']
    elif type(r) in (tuple, list) and len(r) >= 1 and r[0] == 'graph':
        start_response('200 OK', [('Content-Type', 'image/svg+xml')])
        r = r[1]
    else:
        start_response('200 OK', [('Content-Type', 'text/html;charset=utf8')])

    return [r]

def general():
    tmpl = jinjaenv.get_template('base.html')

    return str(tmpl.render(
        {   'topusers' : ut.top(_limit=5), 'topscripts' : st.top(_limit=5)}
        ))


def user(userid=None):
    tmpl = jinjaenv.get_template('user.html')
    uinfo = ut.info(userid)

    return str(tmpl.render(
        {   'topusers' : ut.top(_limit=5), 'topscripts' : st.top(_limit=5),
            'ttc' : uinfo['time'][1],
            'tc' : uinfo['time'][0], 'user' : uinfo['user']}
        ))

def user_commit(userid=None, pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('usercommits.html')
    user = session.query(User).filter(User.id==userid).first()

    return str(tmpl.render(
        {   'topusers' : ut.top(_limit=5), 'topscripts' : st.top(_limit=5),
            'user' : user, 'commits' : ut.listc(user, 
                (pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE)}
        ))

def script(scriptid=None):
    tmpl = jinjaenv.get_template('script.html')
    sinfo = st.info(scriptid)

    return str(tmpl.render(
        {   'topusers' : ut.top(_limit=5), 'topscripts' : st.top(_limit=5),
            'ttc' : sinfo['time'][1], 'tc' : sinfo['time'][0],
            'script' : sinfo['script'], 'vars' : sinfo['vars']}
        ))

def script_commit(scriptid=None,pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('scriptcommits.html')
    script = session.query(Script).filter(Script.id==scriptid).first()

    return str(tmpl.render(
        {   'topusers' : ut.top(_limit=5), 'topscripts' : st.top(_limit=5),
            'script' : script, 'commits' : st.listc(script,
                (pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE)}
        ))

def script_graph(scriptid=None):
    sinfo = st.info(scriptid)

    vars = sinfo['vars']
    script = sinfo['script']

    fracs = []
    labels = []

    for x in vars:
        fracs.append(x[0])
        labels.append(x[1])

    s = gt.pie(fracs,labels,'Variables for %s' % script.name)
    return ['graph', s]

def users(pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('users.html')

    return str(tmpl.render(
        {   'topusers' : ut.top(_limit=5), 'topscripts' : st.top(_limit=5),
            'users' : ut.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'pageid' : pageid   }
        ))

def scripts(pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('scripts.html')

    return str(tmpl.render(
        {   'topusers' : ut.top(_limit=5), 'topscripts' : st.top(_limit=5),
            'scripts' : st.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'pageid' : pageid   }
        ))


if __name__ == '__main__':
    jinjaenv = Environment(loader=PackageLoader('stats', 'templates'))
    wt = WebTool()
    ut = UserTool(session)
    st = ScriptTool(session)
    gt = GraphTool()

    import re
    # Regex rules to call the right stuff on the right url.
    # May eventually turn it all into one regex? Would make it less readable
    # though.

    # XXX: TODO: Integers hard limited at 6 chars max. Python has unlimited
    # integers; but databases do not. If someone passes 999999999999999999
    # then we will get a database error. This ``fix'' works around it.
    # Until you get more than 999999 users.
    wt.add_rule(re.compile('^%s/user/([0-9]{1,6})$' % BASE_URL),
            user, ['userid'])

    wt.add_rule(re.compile('^%s/user/([0-9]{1,6})/commits$' \
            % BASE_URL), user_commit, ['userid'])

    wt.add_rule(re.compile('^%s/user/([0-9]{1,6})/commits/([0-9]{1,6})?$' \
            % BASE_URL), user_commit, ['userid', 'pageid'])


    # Two rules. We don't want to match /user/all10
    wt.add_rule(re.compile('^%s/user/all/?$' % BASE_URL),
            users, [])

    wt.add_rule(re.compile('^%s/user/all/([0-9]{1,6})?$' % BASE_URL),
            users, ['pageid'])

    wt.add_rule(re.compile('^%s/script/([0-9]{1,6})$' % BASE_URL),
            script, ['scriptid'])

    wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/commits$' \
            % BASE_URL), script_commit, ['scriptid'])

    wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/commits/([0-9]{1,6})?$' \
            % BASE_URL), script_commit, ['scriptid', 'pageid'])

    wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/graph$' % BASE_URL),
            script_graph, ['scriptid'])

    # Two rules (see above)
    wt.add_rule(re.compile('^%s/script/all/?$' % BASE_URL),
            scripts, [])

    wt.add_rule(re.compile('^%s/script/all/([0-9]{1,6})?$' % BASE_URL),
            scripts, ['pageid'])

    wt.add_rule(re.compile('^%s/?$' % BASE_URL),
                general, [])

    # One rule to rule them all...
    # ^%s/(user|script|commit)/all/?([0-9]{1,6}?/?$

    WSGIServer(stats).run()

