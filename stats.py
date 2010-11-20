#!/usr/bin/env python

# TODO:
# Fix templates so not every child has to get data for the ``total'' stats
# as well.

# Routes:
# /graph for graphs? (filetype png/svg?)
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
from webtool import WebTool, read_post_data

# Import UserTool
from query import UserTool, ScriptTool, CommitTool
from graph import GraphTool

# For date & time utils
import datetime

from beaker.middleware import SessionMiddleware

# Import config
from config import BASE_URL, RESULTS_PER_PAGE, \
    session_options

def get_pageid(pageid):
    try:
        return max(int(pageid), 1)
    except (ValueError, TypeError):
        return 1

def template_render(template, vars, default_page=True):
    vars['_import'] = {'datetime' : datetime}
    if default_page:
        vars['topusers']    = ut.top(_limit=5)
        vars['topscripts']  = st.top(_limit=5)
        vars['lastcommits'] = ct.top(_limit=5)

    return template.render(vars)


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

/login              |   Login form (GET) and login API (POST)
/logout             |   Delete session


==== TODO / Unfinished ====
/api/commit
    POST Data:
        User / Pass
        Script
        Minutes
        Extra vars

Add /:format?
/api/scriptinfo/:id
/api/userinfo/:id
"""

def stats(env, start_response):
#    session = env['beaker.session']

    r = wt.apply_rule(env['REQUEST_URI'], env)

    if r is None:
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        r = '404: %s' % env['REQUEST_URI']
    elif type(r) in (tuple, list) and len(r) >= 1 and r[0] == 'graph':
        start_response('200 OK', [('Content-Type', 'image/svg+xml')])
        r = r[1]
    else:
        start_response('200 OK', [('Content-Type', 'text/html;charset=utf8')])

    return [r]

def general(env):
    tmpl = jinjaenv.get_template('base.html')

    return str(template_render(tmpl, {'session' : env['beaker.session']} ))

def user(env, userid=None):
    tmpl = jinjaenv.get_template('user.html')
    uinfo = ut.info(userid)

    if uinfo is None:
        return None

    return str(template_render(tmpl,
        {   'ttc' : uinfo['time'][1], 'tc' : uinfo['time'][0],
            'user' : uinfo['user'], 'session' : env['beaker.session'] }
        ))

def user_commit(env, userid=None, pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('usercommits.html')
    user = session.query(User).filter(User.id==userid).first()

    return str(template_render(tmpl,
        {   'user' : user, 'commits' : ut.listc(user, 
                (pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'session' : env['beaker.session']}
        ))

def script(env, scriptid=None):
    tmpl = jinjaenv.get_template('script.html')
    sinfo = st.info(scriptid)

    if sinfo is None:
        return None

    return str(template_render(tmpl,
        {   'ttc' : sinfo['time'][1], 'tc' : sinfo['time'][0],
            'script' : sinfo['script'], 'vars' : sinfo['vars'],
            'session' : env['beaker.session']}
        ))

def script_commit(env, scriptid=None,pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('scriptcommits.html')
    script = session.query(Script).filter(Script.id==scriptid).first()

    return str(template_render(tmpl,
        {   'script' : script, 'commits' : st.listc(script,
                (pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'session' : env['beaker.session']}
        ))

def script_graph(env, scriptid=None):
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

def commit(env, commitid=None):
    tmpl = jinjaenv.get_template('commit.html')
    _commit = ct.info(commitid)
    
    if _commit is None:
        return None

    return str(template_render(tmpl,
        {   'commit' : _commit, 'session' : env['beaker.session']}
        ))

def users(env, pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('users.html')

    return str(template_render(tmpl,
        {   'users' : ut.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'pageid' : pageid, 'session' : env['beaker.session']}
        ))

def scripts(env, pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('scripts.html')

    return str(template_render(tmpl,
        {   'scripts' : st.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'pageid' : pageid, 'session' : env['beaker.session']}
        ))

def commits(env, pageid=None):
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('commits.html')

    return str(template_render(tmpl,
        {   'commits' : ct.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'pageid' : pageid, 'session' : env['beaker.session']}
        ))

def login(env):
    tmpl = jinjaenv.get_template('loginform.html')

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)

        # Does the user exist?
        if session.query(User).filter(User.name ==
                data['user']).filter(User.password == data['pass']).all():

            env['beaker.session']['loggedin'] = True
            env['beaker.session'].save()
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginsuccess' : True} ))
        else:
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginfail' : True}  ))

    elif str(env['REQUEST_METHOD']) == 'GET':

        return str(template_render(tmpl,
            {   'session' : env['beaker.session']}  ))
    else:
        return None

        return env['REQUEST_METHOD'] + str(type(env['REQUEST_METHOD']))
        # Debug ^

def logout(env):
    tmpl = jinjaenv.get_template('base.html')

    s = env['beaker.session']
    s.delete()

    return str(template_render(tmpl, dict()))

def api_commit(env):
    if str(env['REQUEST_METHOD']) != 'POST':
        # 404
        return None

    data = read_post_data(env)

    # TODO: Filter for allowed keywords. (No bogus keywords)
    # TODO: Filter for keywords that must exist

    if not 'user' in data or not 'password' in data:
        return '110'

    user = session.query(User).filter(User.name == data['user']).filter(
            User.password == data['password']).first()
    if not user:
        return '110'

    del data['user']
    del data['password']

    if not 'script' in data:
        return '120'

    script = session.query(Script).filter(Script.id == data['script']).first()

    if not script:
        return '120'

    del data['script']

    if not 'time' in data:
        return '130'

    try:
        time = data['time']
    except ValueError:
        return '130'

    if time < 1:
        return '130'

    del data['time']

    script_vars = dict(zip([x.name.lower() for x in script.variables], 
        script.variables))

    randoms = session.query(Variable).filter(Variable.is_var==0).all()
    r = dict(zip([x.name.lower() for x in randoms], randoms))
    script_vars.update(r)

    vars = dict()

    # TODO: Query random vars
    # random_vars = 

    for x, y in data.iteritems():
        # TODO: Randoms are always allowed
        x = x.lower()
        if x not in script_vars:
            return '140'
        try:
            v = int(y)
        except ValueError:
            return '150'

        vars[script_vars[x]] = v

    res = ct.add(user, script, time, vars)
    if not res:
        return '160'

    return '100'

def api_scriptinfo(env):
    pass

def api_userinfo(env):
    pass

if __name__ == '__main__':
    jinjaenv = Environment(loader=PackageLoader('stats', 'templates'))
    wt = WebTool()
    ut = UserTool(session)
    st = ScriptTool(session)
    ct = CommitTool(session)
    gt = GraphTool()

    # Add all rules
    execfile('rules.py')

    WSGIServer(SessionMiddleware(stats, session_options)).run()
