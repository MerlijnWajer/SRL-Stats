#!/usr/bin/env python

# Routes:
# /graph for graphs? (filetype png/svg?)
# /var for var pages ex: /var/42

# HAX.
import os
os.environ['MPLCONFIGDIR'] = '/tmp'

from flup.server.fcgi import WSGIServer
from jinja2 import Environment, PackageLoader
from sql import User, Script, Variable, Commit, CommitVar, Base, session
from webtool import WebTool, read_post_data

# Import UserTool
from query import UserTool, ScriptTool, CommitTool, VariableTool
from graph import GraphTool

# For date & time utils
import datetime

# For regex
import re

from beaker.middleware import SessionMiddleware

# Import config
from config import BASE_URL, RESULTS_PER_PAGE, \
    session_options

# Log levels
LVL_ALWAYS = 0          # Will always be shown.
LVL_NOTABLE = 42        # Notable information.
LVL_INFORMATIVE = 314   # Informative
LVL_VERBOSE = 666       # Verbose information. This should be everything except
                        # stuff like what variables contain.

def get_pageid(pageid):
    try:
        return max(int(pageid), 1)
    except (ValueError, TypeError):
        return 1

def template_render(template, vars, default_page=True):
    vars['_import'] = {'datetime' : datetime}
    if default_page:
        vars['topusers']    = ut.top(_limit=4)
        vars['topscripts']  = st.top(_limit=4)
        vars['lastcommits'] = ct.top(_limit=4)
        vars['topvars']     = vt.top(_limit=4, only_vars=True)
        vars['baseurl']     = BASE_URL

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

/variable/id:       |   Variable Info.

/login              |   Login form (GET) and login API (POST)
/logout             |   Delete session

/api/commit
    POST Data:
        User / Pass
        Script
        Minutes
        Extra vars

TODO:
Add /:format?
/api/scriptinfo/:id
/api/userinfo/:id

/manage/scripts/            |   List scripts, link to /manage/script/scriptid
/manage/script/:scriptid    |   Show script vars. Allow people to add vars to
                            |   their script. (But not create not vars, nor
                            |   delete vars from their script)

/manage/variables           |   Add variables to the system.

/manage/commits/            |   For admins? Delete commits?
/manage/users/              |   For admins?
/manage/user                |   ?
"""

def stats(env, start_response):
    log.log([], LVL_VERBOSE, PyLogger.INFO, 'Request for %s by %s' % \
            (env['REQUEST_URI'], env['REMOTE_ADDR']))

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

def loggedin(env):
    """
        Return true when logged in.
    """
    if 'loggedin' in env['beaker.session']:
        return env['beaker.session']['loggedin'] is True
    return False

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
            'pageid' : pageid,
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
            'pageid' : pageid,
            'session' : env['beaker.session']}
        ))

def script_graph(env, scriptid=None):
    sinfo = st.info(scriptid)
    if sinfo is None:
        return None
#
    vars = sinfo['vars']
    script = sinfo['script']
#    from sqlalchemy import func
#    vars = session.query(Script.name, User.name,
#            func.sum(Commit.timeadd)).join((Commit, Commit.script_id ==
#                Script.id)).join((User, User.id ==
#                    Commit.user_id)).filter(Script.id==1).group_by(Script.name,
#                            User.name).all()
#

    fracs = []
    labels = []

    for x in vars:
        fracs.append(x[0])
        #fracs.append(x[2])
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

def variable(env, variableid=None):
    tmpl = jinjaenv.get_template('variable.html')
    _variable = vt.info(variableid)

    if _variable is None:
        return None

    return str(template_render(tmpl,
        {   'variable' : _variable['variable'], 'amount' :
            _variable['amount'][0],
            'session' : env['beaker.session'] }
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

def variables(env, pageid=None):
    # FIXME
    pass

def login(env):
    tmpl = jinjaenv.get_template('loginform.html')

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)

        # Does the user exist?
        res =  session.query(User).filter(User.name ==
                data['user']).filter(User.password == data['pass']).first()
        if res:
            env['beaker.session']['loggedin'] = True
            env['beaker.session']['loggedin_id'] = res.id
            env['beaker.session']['loggedin_name'] = res.name
            env['beaker.session'].save()
            log.log([], LVL_NOTABLE, PyLogger.INFO,
                    'Login %s : %s' % (env['REMOTE_ADDR'], data['user']))
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginsuccess' : True} ))
        else:
            log.log([], LVL_NOTABLE, PyLogger.INFO,
                    'Failed login %s : %s' % (env['REMOTE_ADDR'], data['user']))
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginfail' : True}  ))

    elif str(env['REQUEST_METHOD']) == 'GET':

        return str(template_render(tmpl,
            {   'session' : env['beaker.session']}  ))
    else:
        return None

def logout(env):
    tmpl = jinjaenv.get_template('base.html')

    s = env['beaker.session']
    s.delete()

    log.log([], LVL_NOTABLE, PyLogger.INFO,
            'Logut %s' % env['REMOTE_ADDR'])

    return str(template_render(tmpl, dict()))

def api_commit(env):
    if str(env['REQUEST_METHOD']) != 'POST':
        # 404
        return None

    data = read_post_data(env)


    # XXX FIXME This is ugly
    pd = data.copy()
    pd['password'] = 'xxxxxxxx'
    log.log([], LVL_INFORMATIVE, PyLogger.INFO,
            'API_COMMIT: %s, %s' % (env['REMOTE_ADDR'], pd))


    # XXX: Check username. injection is not possible afaik? Check anyway.
    # XXX: Also, space in name is '+' (POST RFC)
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

def manage_scripts(env):
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return str(template_render(tmpl,
            {   'session' : env['beaker.session']}  ))
    
    user = session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

    tmpl = jinjaenv.get_template('managescripts.html')

    return str(template_render(tmpl, 
        {   'session' : env ['beaker.session'],
            'user' : user } ))

    # If we get to here, we are logged in.
def manage_script(env, scriptid):
    if not loggedin:
        tmpl = jinjaenv.get_template('loginform.html')
        return str(template_render(tmpl,
            {   'session' : env['beaker.session']}  ))

    script = session.query(Script).filter(Script.id == scriptid).first()
    
    if not script:
        return None

    tmpl = jinjaenv.get_template('scriptmanage.html')

    return str(template_render(tmpl,
        { 'session' : env ['beaker.session'],
            'script' : script
            }))

if __name__ == '__main__':
    jinjaenv = Environment(loader=PackageLoader('stats', 'templates'))
    wt = WebTool()
    ut = UserTool(session)
    st = ScriptTool(session)
    ct = CommitTool(session)
    vt = VariableTool(session)
    gt = GraphTool()

    from log import PyLogger

    log = PyLogger()

    verbosity = LVL_VERBOSE

    log.assign_logfile('/tmp/stats.log', verbosity, (PyLogger.WARNING,
        PyLogger.INFO))
    log.assign_logfile('/tmp/stats.err', verbosity, (PyLogger.ERROR,))
    log.log([], LVL_ALWAYS, PyLogger.INFO, 'Starting the SRL-Stats server')

    # Add all rules
    execfile('rules.py')

    usermatch = re.compile('^[0-9|A-Z|a-z]+$')

    WSGIServer(SessionMiddleware(stats, session_options)).run()
