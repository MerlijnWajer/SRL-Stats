# Find exact depends?
from sqlalchemy import *
from classes import User, Script, Variable, Commit, CommitVar, Base

class UserTool(object):

    def __init__(self, sess):
        self.s = sess

    def top(self, limit):
        return self.s.query(func.sum(Commit.timeadd), User.name, User.id).join(
            (User, Commit.user_id == User.id)).group_by(
             User.name, User.id).order_by(desc('sum_1')).limit(limit)
    
    def info(self, uid):
        user = self.s.query(User).filter(User.id==uid).first()
        time = self.s.query(func.count(Commit.timeadd), 
                func.sum(Commit.timeadd)).join(
                (User, Commit.user_id == User.id)).filter(
                User.id == uid).first()

        return dict(zip(['user', 'time'], [user, time]))

    def list(self, user):
        commits = self.s.query(Commit).join((User,
            User.id==Commit.user_id)).filter(User.id == \
                    user.id).order_by(desc(Commit.id)).all()
        return commits

class ScriptTool(object):

    def __init__(self, sess):
        self.s = sess

    def top(self, limit):
        return self.s.query(func.sum(Commit.timeadd), Script.name, Script.id \
                ).join(
            (Script, Commit.script_id == Script.id)).group_by(
             Script.name, Script.id).order_by(desc('sum_1')).limit(limit)
    
    def info(self, sid):
        script = self.s.query(Script).filter(Script.id==sid).first()
        vars = self.s.query(func.sum(CommitVar.amount), Variable.name).join(
                (Variable, CommitVar.variable_id==Variable.id)).join(
                (Commit, Commit.id == CommitVar.commit_id)).filter(
                 Commit.script_id == sid).group_by(Variable.name).all()
        time = self.s.query(func.count(Commit.timeadd), 
                func.sum(Commit.timeadd)).join(
                (Script, Commit.script_id == Script.id)).filter(
                Script.id == sid).first()

        return dict(zip(['script', 'vars', 'time'], [script, vars, time]))

    def list(self, script):
        commits = self.s.query(Commit).join((Script,
            Script.id==Commit.script_id)).filter(Script.id == \
                    script.id).order_by(desc(Commit.id)).all()
        return commits
