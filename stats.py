#!/usr/bin/env python

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, Response, jsonify

from flask.ext.sqlalchemy import SQLAlchemy

from classes import User, Script, Commit, Variable, CommitVar, \
    UserScriptCache, UserScriptVariableCache

from query import UserTool, ScriptTool, CommitTool, VariableTool

from database import db_session

import datetime, time
import json

###############################################################################
# TODO:
#   -   Make sure <int:foo> passed by URLs are not larger than the database
#       can handle.
#   -   Make sure the pageid is not negative.
#   -   Use WTForms for login/register forms.
#   -   Graph support once again
#   -   Make database cache incremental. (In query.CommitTool.add)
#       I've taken initial steps. However, several things remain:
#
#           -   We need to calculate the initial cache. (Move this to an
#               external script? Or at least a seperate file)
#           -   We need to make sure it is serialised. (Use transactions)
#                   c = db_session.connection() should do the trick.
#                   With the connection object we can do stuff like c.begin(),
#                   etc.
#           -   We need to make sure the cache also generates entries for
#               scripts that have no commits, or for scripts that do not (yet)
#               own a specific variable. (Or we can create them when creating a
#               variable / doing a first commit, might be easier and save table
#               size)
#           -   We need to actually test if this will completely fix the cache.
#
#   -   Add SimpleCache support (cache.get|set)
#
###############################################################################


###############################################################################
# Configuration
USE_OWN_HTTPD = True
DEBUG = True
RESULTS_PER_PAGE=15
###############################################################################

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_pyfile('stats-config.py')
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

# Do I need these two lines?
from database import init_db
init_db()

@app.teardown_request
def shutdown_session(exception=None):
    """
    Free the scoped session:

        To use SQLAlchemy in a declarative way with your application, you just
        have to put the following code into your application module. Flask
        will automatically remove database sessions at the end of the request
        for you.
    """
    db_session.remove()

class StatsEncoder(json.JSONEncoder):
    def default(self, o):
        if type(o) in (User, Variable, Script):
            return o.name
        if type(o) in (Commit,):
            return dict(id=o.id, user_id=o.user_id, script_id=o.script_id,
            timeadd=o.timeadd,
            timestamp=time.mktime(o.timestamp.timetuple()) * 1000,
            commitvars=o.commitvars
            )
        if type(o) in (CommitVar,):
            return dict(commit_id=o.commit_id, variable_id=o.variable_id,
                    amount=o.amount)#, commit=o.commit, variable=o.variable)
        return json.JSONEncoder.default(self, o)

def s_jsonify(o):
    return json.dumps(o, cls=StatsEncoder)

def stats_render_template(template, **kw):
    """
        Template Render is a helper that initialises basic template variables
        and handles unicode encoding.
    """
    kw['_import'] = {'datetime' : datetime}

    return render_template(template, **kw)

@app.route('/user/<int:userid>')
def user(userid):
    """
    User-specific information.
    """
    u = ut.info(userid, cache=True)

    return s_jsonify(u)

#    return stats_render_template('user.html',
#        ttc=u['time']['commit_time'],
#        tc=u['time']['commit_amount'],
#        vars=u['vars'],
#        user=u['user'],
#        )

@app.route('/user/all')
@app.route('/user/all/<int:pageid>')
def users(pageid=0):
    """
    List of users.
    """
    top_users = ut.top(pageid * RESULTS_PER_PAGE, RESULTS_PER_PAGE, cache=True)
    return s_jsonify(top_users)

@app.route('/user/<int:userid>/commits')
@app.route('/user/<int:userid>/commits/<int:pageid>')
def user_commits(userid, pageid=0):
    """
    Users Commits.
    """
    u = db_session.query(User).filter(User.id==userid).first()
    uc = ut.listc(u, pageid * RESULTS_PER_PAGE, RESULTS_PER_PAGE)
    return s_jsonify(uc)

@app.route('/user/<int:userid>/script/<int:scriptid>')
def user_scripts(userid, scriptid):
    """
    Information for a script specific to a user.
    """
    abort(403)

@app.route('/user/<int:userid>/script/<int:scriptid>/commits')
@app.route('/user/<int:userid>/script/<int:scriptid>/commits/<int:pageid>')
def user_commits_script(userid, scriptid, pageid=0):
    """
    List of commits to a script by a specific user.
    """
    abort(403)


@app.route('/script/<int:scriptid>')
def script(scriptid):
    """
    Script-specific information.
    """
    abort(403)

@app.route('/script/all')
@app.route('/script/all/<int:pageid>')
def scripts(pageid=0):
    """
    List of Scripts.
    """
    abort(403)

@app.route('/script/<int:scriptid>/commits')
@app.route('/script/<int:scriptid>/commits')
def script_commits(scriptid, pageid=0):
    abort(403)

@app.route('/commit/<int:commitid>')
def commit(commitid):
    """
    Commit-specific information.
    """
    c = ct.info(commitid)
    return s_jsonify(c)
    abort(403)

@app.route('/commit/all')
@app.route('/commit/all/<int:pageid>')
def commits():
    """
    List of commits.
    """
    abort(403)

@app.route('/variable/<int:variableid>')
def variable(variableid):
    """
    Variable-specific information.
    """
    abort(403)

@app.route('/variable/all')
@app.route('/variable/all/<int:pageid>')
def variables(pageid=0):
    abort(403)

@app.route('/login')
def login():
    abort(403)

@app.route('/logout')
def logout():
    abort(403)

@app.route('/register')
def register():
    abort(403)

class PrefixWith(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        app_root = app.config['APPLICATION_ROOT']
        if environ['PATH_INFO'].startswith(app_root):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(app_root):]
            environ['SCRIPT_NAME'] = app_root
        else:
            environ['PATH_INFO'] = '/GENERIC-404'
            environ['SCRIPT_NAME'] = ''
            #start_response('404 Not Found', [('Content-Type', 'text/plain')])
            #return '404'

        return app(environ, start_response)


if __name__ == '__main__':
    ut = UserTool(db_session)
    ct = CommitTool(db_session)
    st = ScriptTool(db_session)
    vt = VariableTool(db_session)

    if USE_OWN_HTTPD:
        app.run()
    else:
        application = PrefixWith(app)
        from flup.server.fcgi import WSGIServer
        WSGIServer(application).run()

