#!/usr/bin/env python
"""
Stats Module. Run this via fcgi.
"""

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

# JSON for /api/
import simplejson as json

# Import config
from config import BASE_URL, RESULTS_PER_PAGE, \
    session_options

# Log levels
LVL_ALWAYS = 0          # Will always be shown.
LVL_NOTABLE = 42        # Notable information.
LVL_INFORMATIVE = 314   # Informative
LVL_VERBOSE = 666       # Verbose information. This should be everything except
                        # stuff like what variables contain.

# We use this to check input for sanity.
alphanumspace = re.compile('^[0-9,A-z, ]+$')

def get_pageid(pageid):
    try:
        return max(int(pageid), 1)
    except (ValueError, TypeError):
        return 1

def template_render(template, vars, default_page=True):
    vars['_import'] = {'datetime' : datetime}
    vars['baseurl'] = BASE_URL

    if default_page:
        vars['topusers']    = ut.top(_limit=4)
        vars['topscripts']  = st.top(_limit=4)
        vars['lastcommits'] = ct.top(_limit=4)
        vars['topvars']     = vt.top(_limit=4, only_vars=True)

    return template.render(vars)


# URLs:
"""
/user/:id           |   User Info (Total Commits, etc) Owned Scripts
/user/:id/commits   |   User Commits
/user/all/(:pageid) |   All users. (With possible pid)

/user/id:/script/:id|   User data to specific script.

/user/id:/script/:id/commits/(:pageid)
                    |   User commits to specific script.

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

/manage/scripts/            |   List scripts, link to /manage/script/scriptid
                            |   Allow script creation
/manage/script/:scriptid    |   Show script vars. Allow people to add vars to
                            |   their script. (But not create not vars, nor
                            |   delete vars from their script)

/api/script/:id             |   Get script info in JSON
/api/user/:id               |   Get user info in JSON
/api/commit/last            |   Get last commit info in JSON

TODO
/user/:id/scripts   |   All scripts user committed to
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
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        tmpl = jinjaenv.get_template('404.html')

        return str(template_render(tmpl, {'url' : env['REQUEST_URI']}, default_page=False))
    elif type(r) in (tuple, list) and len(r) >= 1 and r[0] == 'graph':
        start_response('200 OK', [('Content-Type', 'image/svg+xml')])
        r = r[1]
    elif type(r) in (tuple, list) and len(r) >= 1:
        start_response('200 OK', [('Content-Type', r[0])])
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
        {   'ttc' : uinfo['time']['commit_time'],
            'tc' : uinfo['time']['commit_amount'],
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
        {   'ttc' : sinfo['time']['commit_time'],
            'tc' :  sinfo['time']['commit_amount'],
            'script' : sinfo['script'], 'vars' : sinfo['vars'],
            'session' : env['beaker.session']
        }
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
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('variables.html')

    return str(template_render(tmpl,
        {   'variables' : vt.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'pageid' : pageid, 'session' : env['beaker.session']}
        ))

def user_script_stats(env, userid, scriptid):
    data = ut.info_script(userid, scriptid)
    if data is None:
        return None

    tmpl = jinjaenv.get_template('userscript.html')

    return str(template_render(tmpl, {
        'user' : data['user'],
        'script' : data['script'],
        'time' : data['time'],
        'vars' : data['vars'],
        'session' : env['beaker.session']}))

def user_script_commits(env, userid, scriptid, pageid):
    pageid = get_pageid(pageid)
    data = ut.listc_script(userid, scriptid,(pageid-1)*RESULTS_PER_PAGE,
            RESULTS_PER_PAGE)

    tmpl = jinjaenv.get_template('userscriptcommits.html')

    return str(template_render(tmpl, {
        'user' : data['user'],
        'script' : data['script'],
        'commits' : data['commits'],
        'pageid' : pageid, 'session' : env['beaker.session']}
        ))
    pass

def login(env):
    tmpl = jinjaenv.get_template('loginform.html')

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)

        if data is None:
            return str('Error: Invalid post data')

        if 'user' not in data or 'pass' not in data:
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginfail' : True}  ))

        data['user'] = data['user'].replace('+', ' ')
        data['pass'] = data['pass'].replace('+', ' ')

        if not alphanumspace.match(data['user']):
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginfail' : True}  ))

        if not alphanumspace.match(data['pass']):
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginfail' : True}  ))

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


    if not 'user' in data or not 'password' in data:
        return '110'

    data['user'] = data['user'].replace('+', ' ')
    data['password'] = data['password'].replace('+', ' ')

    # Space in name is '+' (POST RFC)
    if not alphanumspace.match(data['user']):
        return '110'

    if not alphanumspace.match(data['password']):
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

    for x, y in data.iteritems():
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
            {   'session' : env['beaker.session']} ))
    
    user = session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

    tmpl = jinjaenv.get_template('managescripts.html')

    return str(template_render(tmpl, 
        {   'session' : env ['beaker.session'],
            'user' : user }))

    # If we get to here, we are logged in.

def manage_script(env, scriptid):
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return str(template_render(tmpl,
            {   'session' : env['beaker.session']}  ))

    script = session.query(Script).filter(Script.id == scriptid).first()
    
    if not script:
        return None

    if str(env['REQUEST_METHOD']) == 'POST':
            data = read_post_data(env)

            if data is None:
                return str('Error: Invalid POST data')

            if 'variable' in data:
                try:
                    id = data['variable']
                except ValueError:
                    return str('Invalid POST data: Not a number')

            var = session.query(Variable).filter(Variable.id == id).first()

            if var is None:
                return str('Invalid POST data: No such variable')
            
            if var not in script.variables:
                script.variables.append(var)

            session.commit()

    vars = session.query(Variable).filter(Variable.is_var==1).all()
    vars_intersect = filter(lambda x: x not in script.variables, vars) if \
        script.variables is not None else vars

    tmpl = jinjaenv.get_template('managescript.html')

    return str(template_render(tmpl,
        { 'session' : env ['beaker.session'],
            'script' : script,
            'vars' : vars_intersect
            }))

def create_script(env):
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return str(template_render(tmpl,
            {   'session' : env['beaker.session']}  ))

    tmpl = jinjaenv.get_template('createscript.html')

    if str(env['REQUEST_METHOD']) == 'POST':
            data = read_post_data(env)
            if data is None:
                return str('Error: Invalid POST data')

            if 'script' in data:
                s = data['script']
                s = s.replace('+', ' ')

            if not alphanumspace.match(s):
                return str(template_render(tmpl, { 'session' : env ['beaker.session'],
                    'error' : 'Error: Script contains invalid characters'}))

            res = session.query(Script).filter(Script.name == s).all()
            if res:
                return str(template_render(tmpl, { 'session' : env ['beaker.session'],
                    'error' : 'Error: Script already exists'}))

            user = session.query(User).filter(User.id == \
                    env['beaker.session']['loggedin_id']).first()

            if not user:
                return str(template_render(tmpl, { 'session' : env ['beaker.session'],
                    'error' : 'Error: Invalid user in session?'}))

            script = Script(s)
            script.owner = user

            session.add(script)
            session.commit()

            return str(template_render(tmpl, { 'session' : env ['beaker.session'],
                  'newscript' : script }))

    return str(template_render(tmpl,
        { 'session' : env ['beaker.session']
            }))

def register_user(env):
    tmpl = jinjaenv.get_template('registeruser.html')

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)

        if data is None:
            return str('Error: Invalid post data')

        if 'user' not in data or 'pass' not in data:
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'registerfail' : True}  ))

        data['user'] = data['user'].replace('+', ' ')
        data['pass'] = data['pass'].replace('+', ' ')

        if not alphanumspace.match(data['user']):
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'registerfail' : True}  ))

        if not alphanumspace.match(data['pass']):
            return str(template_render(tmpl,
            {   'session' : env['beaker.session'], 'registerfail' : True}  ))

        # Does the user exist?
        res =  session.query(User).filter(User.name ==
                data['user']).filter(User.password == data['pass']).first()

        user = User(data['user'], data['pass'])

        session.add(user)
        session.commit()

        return str(template_render(tmpl,
            { 'session' : env['beaker.session'], 'registersuccess' : True} ))

    elif str(env['REQUEST_METHOD']) == 'GET':
        return str(template_render(tmpl,
            {   'session' : env['beaker.session']}  ))
    else:
        return None

def signature_api_script(env, scriptid):
    info = st.info(scriptid)

    if info is None:
        return None

    last_commit = st.listc(info['script'], _limit=1)

    if last_commit and len(last_commit):
        last_commit = last_commit[0]

    return ['text/plain', json.dumps({
            'script' : info['script'].name,
            'owner' : info['script'].owner.name,
            'commits' : info['time']['commit_amount'],
            'time' : info['time']['commit_time'],
            'vars' : info['vars'],
            'last_commit_on:' : last_commit.timestamp.ctime() if last_commit else
            None,
            'last_commit_by:' : last_commit.user.name if last_commit else
            None
        })]

    # TODO:
    # Add more info: Last commit by, Last commit on.

def signature_api_user(env, userid):
    info = ut.info(userid)

    if info is None:
        return None

    return ['text/plain', json.dumps({
        'user' : info['user'].name,
        'time' : info['time']['commit_time'],
        'commits' : info['time']['commit_amount']
        })]

    # TODO:
    # Add more info: Last commit to, Last commit on.

def signature_api_commit(env):
    info = ct.top(_limit=1)

    if not info:
        return None

    commit = info[0]

    return ['text/plain', json.dumps({
        'script' : commit.script.name,
        'user' : commit.user.name,
        'time_added' : commit.timeadd,
        'timestamp' : commit.timestamp.ctime()
        })]

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
