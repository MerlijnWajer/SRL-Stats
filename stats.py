#!/usr/bin/env python
"""
Stats Module. Run this via fcgi.
The Stats module glues all the components together into a function website.
In short, every URL is defined by some *rule* and each rule has its own method.
Then, based on the URL; a template is loaded and required variables are
loaded.
"""

# Routes:
# /graph for graphs? (filetype png/svg?)
# /var for var pages ex: /var/42

# HAX.
import os
os.environ['MPLCONFIGDIR'] = '/tmp'

from flup.server.fcgi import WSGIServer
from jinja2 import Environment, PackageLoader
from sql import User, Script, Variable, Commit, CommitVar, Base, Session
from webtool import WebTool, read_post_data

# Import UserTool
from query import UserTool, ScriptTool, CommitTool, VariableTool
from graph import GraphTool

# For date & time utils
import datetime

# For unquote
import urllib

# For regex
import re

# For password hashes
import hashlib

from beaker.middleware import SessionMiddleware

# JSON for /api/
import simplejson as json

# Import config
from config import BASE_URL, RESULTS_PER_PAGE, \
    session_options


# XXX: Perhaps move this to query. (Also move all commit extraction to query)
from sqlalchemy import func
from sqlalchemy import extract
import sqlalchemy

# Log levels
LVL_ALWAYS = 0          # Will always be shown.
LVL_NOTABLE = 42        # Notable information.
LVL_INFORMATIVE = 314   # Informative
LVL_VERBOSE = 666       # Verbose information. This should be everything except
                        # stuff like what variables contain.

# We use this to check input for sanity.
alphanumspace = re.compile('^[0-9,A-z, ]+$')
emailre = re.compile('^[A-z,0-9,\._-]+@[A-z0-9.-]+\.[A-z]{2,6}$')

def get_pageid(pageid):
    """
        Parses *pageid*; if it is a valid integer; the integer is returned. If
        the integer is < 1; 1 is returned. If it is not an integer; 1 is
        returned as well.
    """
    try:
        return max(int(pageid), 1)
    except (ValueError, TypeError):
        return 1

def template_render(template, vars, default_page=True):
    """
        Template Render is a helper that initialisaes basic template variables
        and handles unicode encoding.
    """
    vars['_import'] = {'datetime' : datetime}
    vars['baseurl'] = BASE_URL
    #vars['uniencode'] = type
    #vars['uniencode'] = lambda x: x.encode('utf8')

    if default_page:
        vars['topusers']    = ut.top(_limit=4)
        vars['topscripts']  = st.top(_limit=4)
        vars['lastcommits'] = ct.top(_limit=4)
        vars['topvars']     = vt.top(_limit=4, only_vars=True)

    return unicode(template.render(vars)).encode('utf8')


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
/manage/variables           |   Add variables to the system.

/api/script/:id             |   Get script info in JSON
/api/user/:id               |   Get user info in JSON
/api/commit/last            |   Get last commit info in JSON

/graph/commit/
/graph/commit/month/:id

/graph/script/:id/month:id
/graph/script/:id/user/:id/month:id

/graph/user/:id/month:id

TODO

/user/:id/scripts           |   All scripts user committed to
/manage/commits/            |   For admins? Delete commits?
/manage/users/              |   For admins?
/manage/user                |   ?
"""

def stats(env, start_response):
    """
        Main function. Handles all the requests.
    """
    log.log([], LVL_VERBOSE, PyLogger.INFO, 'Request for %s by %s' % \
            (env['REQUEST_URI'], env['REMOTE_ADDR']))

    # Search in the known ``rules'' (see rules.py) and call function if
    # existant.
    r = wt.apply_rule(env['REQUEST_URI'], env)

    # Result 'None' means 404.
    if r is None:
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        tmpl = jinjaenv.get_template('404.html')

        return template_render(tmpl, {
            'url' : env['REQUEST_URI'], 'session' : env['beaker.session']},
            default_page=False)

    # XXX: Remove statement in favour of the next
    elif type(r) in (tuple, list) and len(r) >= 1 and r[0] == 'graph':
        start_response('200 OK', [('Content-Type', 'image/png')])
        #start_response('200 OK', [('Content-Type', 'image/svg+xml')])
        r = r[1]
    elif type(r) in (tuple, list) and len(r) >= 1:
        # response with custom type.
        start_response('200 OK', [('Content-Type', r[0])])
        r = r[1]
    else:
        # Normal response.
        start_response('200 OK', [('Content-Type', 'text/html;charset=utf8')])

    return [r]

class SessionHackException(Exception):
    """
    Raised when something goes wrong.
    """

class SessionHack(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, env, start_response):
        try:
            ret = self.app(env, start_response)
        except Exception, e:
            print 'Exception in SessionHack:', e.message
            raise SessionHackException(e.message)
        finally:
            Session.rollback()

        return ret

def loggedin(env):
    """
        Return true when logged in.
    """
    if 'loggedin' in env['beaker.session']:
        return env['beaker.session']['loggedin'] is True
    return False

def general(env):
    """
        Default page.
    """
    tmpl = jinjaenv.get_template('base.html')

    return template_render(tmpl, {'session' : env['beaker.session']} )

def user(env, userid=None):
    """
        User information page. See ``user.html'' for the template.
    """
    tmpl = jinjaenv.get_template('user.html')
    # Also list variables for user.
    uinfo = ut.info(userid)

    if uinfo is None:
        return None

    return template_render(tmpl,
        {   'ttc' : uinfo['time']['commit_time'],
            'tc' : uinfo['time']['commit_amount'],
            'user' : uinfo['user'], 'session' : env['beaker.session'] }
        )

def user_commit(env, userid=None, pageid=None):
    """
        Page with user commits. See ``usercommits.html'' for the template.
    """
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('usercommits.html')

    session = Session()

    user = Session.query(User).filter(User.id==userid).first()
    user_commits = ut.listc(user, (pageid-1)*RESULTS_PER_PAGE,
            RESULTS_PER_PAGE)

    return template_render(tmpl,
        {   'user' : user, 'commits' : user_commits,
            'pageid' : pageid,
            'session' : env['beaker.session']}
        )

def script(env, scriptid=None):
    """
        Script information page. See ``script.html'' for the template.
    """
    tmpl = jinjaenv.get_template('script.html')
    sinfo = st.info(scriptid)

    if sinfo is None:
        return None

    return template_render(tmpl,
        {   'ttc' : sinfo['time']['commit_time'],
            'tc' :  sinfo['time']['commit_amount'],
            'script' : sinfo['script'], 'vars' : sinfo['vars'],
            'session' : env['beaker.session']
        }
        )

def script_commit(env, scriptid=None,pageid=None):
    """
        Page with commits to script. See ``scriptcommits.html'' for the
        template.
    """
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('scriptcommits.html')
    script = Session.query(Script).filter(Script.id==scriptid).first()

    return template_render(tmpl,
        {   'script' : script, 'commits' : st.listc(script,
                (pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE),
            'pageid' : pageid,
            'session' : env['beaker.session']}
        )

def script_graph(env, scriptid=None):
    """
        Experimental function to generate graphs.
        Rather messy at the moment.
    """
    return None
#    sinfo = st.info(scriptid)
#    if sinfo is None:
#        return None
##
#    vars = [(x[0], x[1].name) for x in sinfo['vars']]
#    script = sinfo['script']
##    from sqlalchemy import func
##    vars = session.query(Script.name, User.name,
##            func.sum(Commit.timeadd)).join((Commit, Commit.script_id ==
##                Script.id)).join((User, User.id ==
##                    Commit.user_id)).filter(Script.id==1).group_by(Script.name,
##                            User.name).all()
##
#
#    fracs = []
#    labels = []
#
#    for x in vars:
#        fracs.append(x[0])
#        #fracs.append(x[2])
#        labels.append(x[1])
#
#    s = gt.pie(fracs,labels,'Variables for %s' % script.name)
    return ['graph', s]

def commit(env, commitid=None):
    """
        Page for commit-specific information. See ``commit.html'' for the
        template.
    """
    tmpl = jinjaenv.get_template('commit.html')
    _commit = ct.info(commitid)

    if _commit is None:
        return None

    return template_render(tmpl,
        {   'commit' : _commit, 'session' : env['beaker.session']}
        )

def variable(env, variableid=None):
    """
        Page for information about a variable. See ``variable.html'' for the
        template.
    """
    tmpl = jinjaenv.get_template('variable.html')
    _variable = vt.info(variableid)

    if _variable is None:
        return None

    return template_render(tmpl,
        {   'variable' : _variable['variable'], 'amount' :
            _variable['amount'][0],
            'session' : env['beaker.session'] }
        )

def users(env, pageid=None):
    """
        Page with a list of users.
    """
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('users.html')
    top_users = ut.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE)

    return template_render(tmpl,
        {   'users' : top_users,
            'pageid' : pageid, 'session' : env['beaker.session']}
        )

def scripts(env, pageid=None):
    """
        Page with a list of scripts.
    """
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('scripts.html')
    top_scripts = st.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE)

    return template_render(tmpl,
        {   'scripts' : top_scripts,
            'pageid' : pageid, 'session' : env['beaker.session']}
        )

def commits(env, pageid=None):
    """
        Page with a list of commits.
    """
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('commits.html')
    latest_commits = ct.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE)

    return template_render(tmpl,
        {   'commits' : latest_commits,
            'pageid' : pageid, 'session' : env['beaker.session']}
        )

def variables(env, pageid=None):
    """
        Page with a list of variables.
    """
    pageid = get_pageid(pageid)

    tmpl = jinjaenv.get_template('variables.html')
    top_variables = vt.top((pageid-1)*RESULTS_PER_PAGE, RESULTS_PER_PAGE)

    return template_render(tmpl,
        {   'variables' : top_variables,
            'pageid' : pageid, 'session' : env['beaker.session']}
        )

def user_script_stats(env, userid, scriptid):
    """
        Page with information for a script specific to a user.
    """
    data = ut.info_script(userid, scriptid)
    if data is None:
        return None

    tmpl = jinjaenv.get_template('userscript.html')

    return template_render(tmpl, {
        'user' : data['user'],
        'script' : data['script'],
        'time' : data['time'],
        'vars' : data['vars'],
        'session' : env['beaker.session']})

def user_script_commits(env, userid, scriptid, pageid):
    """
        Page with commits made to a script by a specific user.
    """
    pageid = get_pageid(pageid)
    data = ut.listc_script(userid, scriptid,(pageid-1)*RESULTS_PER_PAGE,
            RESULTS_PER_PAGE)

    tmpl = jinjaenv.get_template('userscriptcommits.html')

    return template_render(tmpl, {
        'user' : data['user'],
        'script' : data['script'],
        'commits' : data['commits'],
        'pageid' : pageid, 'session' : env['beaker.session']}
        )

def login(env):
    """
        Login method. Handles both GET and POST requests.
    """
    tmpl = jinjaenv.get_template('loginform.html')

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)

        if data is None:
            return str('Error: Invalid post data')

        if 'user' not in data or 'pass' not in data:
            return template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginfail' : True}  )

        data['user'] = urllib.unquote_plus(data['user'])
        data['pass'] = urllib.unquote_plus(data['pass'])

        data['pass'] = hashlib.sha256(data['pass']).hexdigest()

        # Does the user exist (and is the password valid)?
        res =  Session.query(User).filter(User.name ==
                data['user']).filter(User.password == data['pass']).first()

        if res:
            env['beaker.session']['loggedin'] = True
            env['beaker.session']['loggedin_id'] = res.id
            env['beaker.session']['loggedin_name'] = res.name

            # XXX: Do not rely on this. Only use for showing permissions where
            # extra checks aren't nessecary. EG: Fine for links, not fine for 
            # actual db changes + access to pages.
            env['beaker.session']['loggedin_level'] = res.admin_level
            env['beaker.session'].save()
            log.log([], LVL_NOTABLE, PyLogger.INFO,
                    'Login %s : %s' % (env['REMOTE_ADDR'], data['user']))
            return template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginsuccess' : True,
                'user' : res} )
        else:
            log.log([], LVL_NOTABLE, PyLogger.INFO,
                    'Failed login %s : %s' % (env['REMOTE_ADDR'], data['user']))
            return template_render(tmpl,
            {   'session' : env['beaker.session'], 'loginfail' : True}  )

    elif str(env['REQUEST_METHOD']) == 'GET':

        return template_render(tmpl,
            {   'session' : env['beaker.session']}  )
    else:
        return None

def logout(env):
    """
        Logout method.
    """
    tmpl = jinjaenv.get_template('base.html')

    s = env['beaker.session']
    s.delete()

    log.log([], LVL_NOTABLE, PyLogger.INFO,
            'Logut %s' % env['REMOTE_ADDR'])

    return template_render(tmpl, dict())

def api_commit(env):
    """
        API to send a commit to the stats system using POST data.
    """
    if str(env['REQUEST_METHOD']) != 'POST':
        # 404
        return None

    data = read_post_data(env)

    if data is None:
        return None

    # XXX FIXME This is ugly
    pd = data.copy()
    pd['password'] = 'xxxxxxxx'
    log.log([], LVL_INFORMATIVE, PyLogger.INFO,
            'API_COMMIT: %s, %s' % (env['REMOTE_ADDR'], pd))


    if not 'user' in data or not 'password' in data:
        return '110'

    data['user'] = urllib.unquote_plus(data['user'])
    data['password'] = urllib.unquote_plus(data['password'])

#    if not alphanumspace.match(data['user']):
#        return '110'
#
#    if not alphanumspace.match(data['password']):
#        return '110'

    data['password'] = hashlib.sha256(data['password']).hexdigest()

    session = Session()

    user = session.query(User).filter(User.name == data['user']).filter(
            User.password == data['password']).first()
    if not user:
        log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: No user' \
                        % (env['REMOTE_ADDR'], pd))
        return '110'

    del data['user']
    del data['password']

    if not 'script' in data:
        log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: No script' \
                        % (env['REMOTE_ADDR'], pd))
        return '120'

    data['script'] = urllib.unquote_plus(data['script'])

    script = session.query(Script).filter(Script.id == data['script']).first()

    if not script:
        log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: Invalid script' \
                        % (env['REMOTE_ADDR'], pd))
        return '120'

    del data['script']

    if not 'time' in data:
        log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: No time' \
                        % (env['REMOTE_ADDR'], pd))
        return '130'

    try:
        time = int(data['time'])
    except ValueError:
        log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: Invalid time (int)' \
                        % (env['REMOTE_ADDR'], pd))
        return '130'

    if time < 5 or time > 60:
        log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: Invalid time (range)' \
                        % (env['REMOTE_ADDR'], pd))
        return '130'

    del data['time']

    randoms = session.query(Variable).filter(Variable.is_var==0).all()

    script_vars = dict(zip([x.name.lower() for x in script.variables], 
        script.variables))

    script_vars.update(dict(zip([x.name.lower() for x in randoms], randoms)))

    script_vars.update(dict(zip([x.id for x in randoms], randoms)))

    script_vars.update(dict(zip([x.id for x in script.variables],
        script.variables)))

    vars = dict()

    for x, y in data.iteritems():
        x = urllib.unquote_plus(x)
        x = x.lower()

        try:
            x = int(x)
        except ValueError:
            pass

        if x not in script_vars:
            log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: Invalid variable for script' \
                        % (env['REMOTE_ADDR'], pd))
            return '140'
        try:
            v = int(y)
        except ValueError:
            log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: Invalid variable value' \
                        % (env['REMOTE_ADDR'], pd))
            return '150'

        if v < 1:
            log.log([], LVL_NOTABLE, PyLogger.WARNING,
                'API_COMMIT: %s, %s DENIED: Invalid variable value (%d)' \
                        % (env['REMOTE_ADDR'], pd, v))
            continue
            # XXX: Add this eventually
            # return '150'

        vars[script_vars[x]] = v

    res = ct.add(user, script, time, vars)
    if not res:
        log.log([], LVL_NOTABLE, PyLogger.WARNING,
            'API_COMMIT: %s, %s DENIED: Internal error' \
                    % (env['REMOTE_ADDR'], pd))
        return '160'

    return '100'

def manage_scripts(env):
    """
        Page to manage scripts.
    """
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return template_render(tmpl,
            {   'session' : env['beaker.session']} )

    user = Session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

    tmpl = jinjaenv.get_template('managescripts.html')

    return template_render(tmpl,
        {   'session' : env ['beaker.session'],
            'user' : user })

def manage_script(env, scriptid):
    """
        Page to manage a specific script. Handles both GET and POST.
    """
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return template_render(tmpl,
            {   'session' : env['beaker.session']}  )

    session = Session()

    user = session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

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

            try:
                session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                session.rollback()
                print 'Rollback in stats.py, manage_script:'
                print 'Postdata:', data
                print 'Exception:', e

    vars = session.query(Variable).filter(Variable.is_var==1).all()
    vars_intersect = filter(lambda x: x not in script.variables, vars) if \
        script.variables is not None else vars

    tmpl = jinjaenv.get_template('managescript.html')

    return template_render(tmpl,
        { 'session' : env ['beaker.session'],
            'script' : script,
            'vars' : vars_intersect
            })

def create_script(env):
    """
        Page to create a script. Handles both GET and POST.
    """
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return template_render(tmpl,
            {   'session' : env['beaker.session']}  )

    session = Session()

    user = session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

    tmpl = jinjaenv.get_template('createscript.html')

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)
        if data is None:
            return str('Error: Invalid POST data')

        if 'script' in data:
            s = data['script']
            s = urllib.unquote_plus(s)
        else:
            return template_render(tmpl, { 'session' : env ['beaker.session'],
                'error' : 'Error: Script contains invalid characters'})

        if len(s) == 0 or len(s) > 20:
            return template_render(tmpl, { 'session' : env ['beaker.session'],
                'error' : 'Error: Script name has invalid length'})

        res = session.query(Script).filter(Script.name == s).all()
        if res:
            return template_render(tmpl, { 'session' : env ['beaker.session'],
                'error' : 'Error: Script already exists'})

        user = session.query(User).filter(User.id == \
                env['beaker.session']['loggedin_id']).first()

        if not user:
            return template_render(tmpl, { 'session' : env ['beaker.session'],
                'error' : 'Error: Invalid user in session?'})

        script = Script(s)
        script.owner = user

        session.add(script)
        try:
           session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            print 'Rollback! create_script.'
            print 'Post data:', data
            print 'Exception:', e

        return template_render(tmpl, { 'session' : env ['beaker.session'],
              'newscript' : script })

    return template_render(tmpl,
        { 'session' : env ['beaker.session']
            })

def create_variable(env):
    """
        Page to create a variable. Handles both GET and POST.
    """
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return template_render(tmpl,
            {   'session' : env['beaker.session']} )

    session = Session()

    user = session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

    if user.admin_level < 1:
        return str('Access denied')

    tmpl = jinjaenv.get_template('createvariable.html')

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)
        if data is None:
            return str('Error: Invalid POST data')

        if 'variable' in data:
            s = data['variable']
            s = urllib.unquote_plus(s)
        else:
            return template_render(tmpl, { 'session' : env ['beaker.session'],
                'error' : 'Error: Variable name not specified'})

        if len(s) == 0 or len(s) > 60:
            return template_render(tmpl, { 'session' : env ['beaker.session'],
                'error' : 'Error: Variable name has invalid length'})

        # 'on' when checked; not in data when not clicked. XXX
        if 'is_var' in data:
            v = 1
        else:
            v = 0

        res = session.query(Variable).filter(Variable.name ==
            s).first()

        if res:
            return template_render(tmpl, { 'session' : env ['beaker.session'],
                'error' : 'Error: Variable already exists'})

        variable = Variable(s, v)
        session.add(variable)
        try:
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            print 'Rollback! create_variable'
            print 'Post data:', data
            print 'Exception:', e

        return template_render(tmpl, { 'session' : env ['beaker.session'],
              'newvariable' : variable})


    return template_render(tmpl,
        {'session' : env['beaker.session'] })

def manage_variable(env, variableid):
    """
        Page to manage a variable. Handles both GET and POST.
    """
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return template_render(tmpl,
            {   'session' : env['beaker.session']} )

    session = Session()

    user = session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

    if user.admin_level < 1:
        return str('Access denied')

    tmpl = jinjaenv.get_template('managevariable.html')

    variable = session.query(Variable).filter(Variable.id == \
            variableid).first()

    if not variable:
        return None

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)

        if data is None:
            return str('Invalid POST data')

        if 'newname' not in data:
            return str('Invalid POST data')

        data['newname'] = urllib.unquote_plus(data['newname'])
        if len(data['newname']) == 0 or len(data['newname']) > 20:
            return template_render(tmpl,
                {   'session' : env ['beaker.session'],
                    'error' : 'Variable name too long.',
                })

        res = session.query(Variable).filter(Variable.name ==
                data['newname']).first()

        if res is None:
            variable.name = data['newname']
            session.add(variable)
            try:
                session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                session.rollback()
                print 'Rollback in manage_variable'
                print 'Post data:', data
                print 'Exception:', e
        else:
            return template_render(tmpl,
                {   'session' : env ['beaker.session'],
                    'error' : 'Name already exists in the system.',
                    'variable' : variable
                })

    return template_render(tmpl,
        {   'session' : env['beaker.session'],
            'variable' : variable
        })


def manage_variables(env, pageid):
    """
        Overview page with variables (manage)
    """
    if not loggedin(env):
        tmpl = jinjaenv.get_template('loginform.html')
        return template_render(tmpl,
            {   'session' : env['beaker.session']} )

    user = Session.query(User).filter(User.id == \
            env['beaker.session']['loggedin_id']).first()

    if not user:
        return None

    if user.admin_level < 1:
        return str('Access denied')

    tmpl = jinjaenv.get_template('managevariables.html')
    pageid = get_pageid(pageid)
    variables =  Session.query(Variable).order_by(Variable.id).offset(\
            (pageid-1) * RESULTS_PER_PAGE).limit(RESULTS_PER_PAGE).all()

    return template_render(tmpl, 
        {   'session' : env ['beaker.session'],
            'variables' : variables,
            'pageid' : pageid,
            'user' : user })

def register_user(env):
    """
        Page to register a user. Handles POST and GET data.
    """
    tmpl = jinjaenv.get_template('registeruser.html')

    session = Session()

    if str(env['REQUEST_METHOD']) == 'POST':
        data = read_post_data(env)

        if data is None:
            return str('Error: Invalid post data')

        if 'user' not in data or 'pass' not in data:
            return template_render(tmpl,
            {   'session' : env['beaker.session'], 'registerfail' : True,
                'error' : 'Post data not complete'}  )

        data['user'] = urllib.unquote_plus(data['user'])
        data['pass'] = urllib.unquote_plus(data['pass'])
        if 'mail' in data:
            data['mail'] = urllib.unquote_plus(data['mail'])

        if len(data['user']) > 20 or len(data['pass']) > 20 or \
           len(data['user']) == 0 or len(data['pass']) == 0:
            return template_render(tmpl,
            {   'session' : env['beaker.session'], 'registerfail' : True,
                'error' : 'Username or Password too long.'}  )

        data['pass'] = hashlib.sha256(data['pass']).hexdigest()

        if 'mail' in data:
            if len(data['mail']) > 40:
                return template_render(tmpl,
            {   'session' : env['beaker.session'], 'registerfail' : True,
                'error' : 'Email address is too long'} )

        log.log([], LVL_VERBOSE, PyLogger.INFO, 'Register POST data: %s' %
                str(data))

        if 'mail' in data and data['mail']:
            if not emailre.match(data['mail']):
                return template_render(tmpl,
                {   'session' : env['beaker.session'], 'registerfail' : True,
                    'error': 'Invalid Email.'}  )

        # Does the user exist?
        res =  session.query(User).filter(User.name ==
                data['user']).first()

        if res:
            return template_render(tmpl,
            {   'session' : env['beaker.session'], 'registerfail' : True,
                'error' : 'Username already exists'}  )


        user = User(data['user'], data['pass'], data['mail'] if 'mail' in data
                else None)

        session.add(user)
        try:
           session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            print 'Rollback in register_user'
            print 'Post data:', data
            print 'Exception:', e

        return template_render(tmpl,
            { 'session' : env['beaker.session'],
               'registersuccess' : True,
               'user' : user} )

    elif str(env['REQUEST_METHOD']) == 'GET':
        return template_render(tmpl,
            {   'session' : env['beaker.session']}  )
    else:
        return None

def signature_api_script(env, scriptid):
    """
        Script Signature API.
    """
    info = st.info(scriptid)

    if info is None:
        return None

    last_commit = st.listc(info['script'], _limit=1)

    if last_commit and len(last_commit):
        last_commit = last_commit[0]

    info['vars'] = [(x[0], x[1].name) for x in info['vars']]

    return ['text/plain', json.dumps({
            'script' : info['script'].name,
            'owner' : info['script'].owner.name,
            'commits' : info['time']['commit_amount'],
            'time' : info['time']['commit_time'],
            'vars' : info['vars'],
            'last_commit_on:' : last_commit.timestamp.ctime() if last_commit
                else None,
            'last_commit_by:' : last_commit.user.name if last_commit else
                None
        }, indent=' ' * 4)]

def signature_api_user(env, userid):
    """
        User Signature API
    """
    # XXX: Also list variables for user
    info = ut.info(userid)

    if info is None:
        return None

    last_commit = ut.listc(info['user'], _limit=1)

    if last_commit and len(last_commit):
        last_commit = last_commit[0]

    return ['text/plain', json.dumps({
            'user' : info['user'].name,
            'time' : info['time']['commit_time'],
            'commits' : info['time']['commit_amount'],
            'last_commit_on:' : last_commit.timestamp.ctime() if last_commit
                else None,
            'last_commit_to:' : last_commit.script.name if last_commit
                else None
        }, indent=' ' * 4)]

def signature_api_commit(env):
    """
        Commit Signature API.
    """
    info = ct.top(_limit=1)

    if not info:
        return None

    commit = info[0]

    return ['text/plain', json.dumps({
        'script' : commit.script.name,
        'user' : commit.user.name,
        'time_added' : commit.timeadd,
        'timestamp' : commit.timestamp.ctime()
        }, indent=' ' * 4)]

def graph_commits(env, month, year, scriptid, userid, select_type):
    if select_type not in ('amount', 'minutes'):
        select_type = 'amount'
    s = graph_commits_month_dyn(env, month, year, scriptid, userid, select_type)
    if s is None:
        return None
    else:
        return ['graph', s]

def graph_commits_month_dyn(env, month=None, year=None,
        scriptid=None, userid=None, select_type='amount'):
    """
        Generic function for month graphs.
        If month is None, the current month is used.
        If year is None, the current year is used.
        Valid select types: 'amount', 'minutes'
    """
    if select_type not in ('amount', 'minutes'):
        return None

    if month is None:
        month = datetime.datetime.now().month
    else:
        month = int(month)

    if month < 1 or month > 12:
        return None

    if year is None:
        year = datetime.datetime.now().year
    else:
        year = int(year)

    if year < 1:
        return None

    if scriptid:
        script = st.info(scriptid)
        if script is None:
            return None

    if userid:
        user = ut.info(userid)
        if user is None:
            return None

    sel = {'amount' : 
                Session.query(extract('day', Commit.timestamp),
                    func.count('*')),
            'minutes':
                Session.query(extract('day', Commit.timestamp),
                    func.sum(Commit.timeadd))
            }
    if select_type not in sel:
        return None

    q = sel[select_type]

    if userid:
        q = q.filter(Commit.user_id==userid)
    if scriptid:
        q = q.filter(Commit.script_id==scriptid)

    q = q.filter(extract('month', Commit.timestamp)==month)
    q = q.filter(extract('year', Commit.timestamp)==year)
    q = q.group_by(extract('day', Commit.timestamp))

    res = q.all()

    amount = range(32)
    for x in range(32):
        amount[x] = 0

    for x in res:
        amount[int(x[0])] = x[1]

    if scriptid:
        title = ' to script: %s' % script['script'].name
    else:
        title = ''

    if userid:
        title += ' by user: %s' % user['user'].name

    s = gt.commit_bar(range(1,33), amount, 
            _title='Commits per day' + title,
            _xlabel='days', _ylabel='%s of commits' % select_type)

    return s

if __name__ == '__main__':
    jinjaenv = Environment(loader=PackageLoader('stats', 'templates'))
    jinjaenv.autoescape = True
    wt = WebTool()
    ut = UserTool(Session)
    st = ScriptTool(Session)
    ct = CommitTool(Session)
    vt = VariableTool(Session)
    gt = GraphTool()

    from log import PyLogger

    log = PyLogger()

    verbosity = LVL_VERBOSE

    from sys import stdout, stderr
    log.assign_logfile(stdout, verbosity, (PyLogger.WARNING,
        PyLogger.INFO))
    log.assign_logfile(stderr, verbosity, (PyLogger.ERROR,))
    log.log([], LVL_ALWAYS, PyLogger.INFO, 'Starting the SRL-Stats server')

    # Add all rules
    execfile('rules.py')

    usermatch = re.compile('^[0-9|A-Z|a-z]+$')

    #WSGIServer(SessionMiddleware(stats,session_options)).run()
    WSGIServer(SessionMiddleware(SessionHack(stats),session_options)).run()
    #WSGIServer(SessionMiddleware(stats, session_options), debug=False).run()
