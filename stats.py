#!/usr/bin/env python

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, Response

from flask.ext.sqlalchemy import SQLAlchemy

from classes import User, Script, Commit, Variable, CommitVar, \
    UserScriptCache, UserScriptVariableCache

from database import db_session

###############################################################################
# TODO:
#   -   Make sure <int:foo> passed by URLs are not larger than the database
#       can handle.
#   -   Make sure the pageid is not negative.
#   -   Use WTForms for login/register forms.
#
###############################################################################


###############################################################################
# Configuration
USE_OWN_HTTPD = True
###############################################################################

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_pyfile('stats-config.py')

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

@app.route('/user/<int:userid>')
def user(userid):
    """
    User-specific information.
    """
    u = db_session.query(User).filter(User.id==userid).first()
    print u
    return str(u)

@app.route('/user/all')
@app.route('/user/all/<int:pageid>')
def users(pageid=1):
    """
    List of users.
    """
    abort(403)


@app.route('/user/<int:userid>/commits')
@app.route('/user/<int:userid>/commits/<int:pageid>')
def user_commits(userid, pageid=1):
    """
    Users Commits.
    """
    abort(403)

@app.route('/user/<int:userid>/script/<int:scriptid>')
def user_scripts(userid, scriptid):
    """
    Information for a script specific to a user.
    """
    abort(403)

@app.route('/user/<int:userid>/script/<int:scriptid>/commits')
@app.route('/user/<int:userid>/script/<int:scriptid>/commits/<int:pageid>')
def user_commits_script(userid, scriptid, pageid=1):
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
def scripts(pageid=1):
    """
    List of Scripts.
    """
    abort(403)

@app.route('/script/<int:scriptid>/commits')
@app.route('/script/<int:scriptid>/commits')
def script_commits(scriptid, pageid=1):
    abort(403)

@app.route('/commit/<int:commitid>')
def commit(commitid):
    """
    Commit-specific information.
    """
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
def variables(pageid=1):
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
    if USE_OWN_HTTPD:
        app.run()
    else:
        application = PrefixWith(app)
        from flup.server.fcgi import WSGIServer
        WSGIServer(application).run()

