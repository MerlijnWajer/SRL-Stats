# Find exact depends?
from sqlalchemy import *
from classes import User, Script, Variable, Commit, CommitVar, Base

class UserTool(object):
    """
        UserTool is a User helper class. It doesn't have to be OOP; and OOP
        may be dropped later on depending whether I still plan to make a 
        caching mechanism or not.
    """

    def __init__(self, sess):
        """
            We need a SQLAlchemy session.
        """
        self.s = sess

    def top(self, _offset=0,_limit=10):
        """
            Return the top *limit* users based on time added.
        """
        return self.s.query(func.sum(Commit.timeadd), User.name, User.id).join(
            (User, Commit.user_id == User.id)).group_by(
             User.name, User.id).order_by(desc('sum_1')).offset(
                     _offset).limit(_limit).all()

    def info(self, uid):
        """
            Returns the user object with id *uid* and the time and commit count
            of the user.
        """
        user = self.s.query(User).filter(User.id==uid).first()
        if user is None:
            return None

        time = self.s.query(func.count(Commit.timeadd), 
                func.sum(Commit.timeadd)).join(
                (User, Commit.user_id == User.id)).filter(
                User.id == uid).first()

        return dict(zip(['user', 'time'], [user, time]))

    def listc(self, user, _offset=0, _limit=10):
        """
            Return the commits made by user.
        """
        commits = self.s.query(Commit).join((User,
            User.id==Commit.user_id)).filter(User.id == \
                    user.id).order_by(desc(Commit.id)).offset(
                    _offset).limit(_limit).all()
        return commits

class ScriptTool(object):

    def __init__(self, sess):
        self.s = sess

    def top(self, _offset=0, _limit=10):
        return self.s.query(func.sum(Commit.timeadd), Script.name, Script.id \
                ).join(
            (Script, Commit.script_id == Script.id)).group_by(
             Script.name, Script.id).order_by(desc('sum_1')).offset(
                     _offset).limit(_limit).all()

    def info(self, sid):
        script = self.s.query(Script).filter(Script.id==sid).first()
        if script is None:
            return None

        vars = self.s.query(func.sum(CommitVar.amount), Variable.name).join(
                (Variable, CommitVar.variable_id==Variable.id)).join(
                (Commit, Commit.id == CommitVar.commit_id)).filter(
                 Commit.script_id == sid).group_by(Variable.name).all()
        time = self.s.query(func.count(Commit.timeadd), 
                func.sum(Commit.timeadd)).join(
                (Script, Commit.script_id == Script.id)).filter(
                Script.id == sid).first()

        return dict(zip(['script', 'vars', 'time'], [script, vars, time]))

    def listc(self, script, _offset=0, _limit=10):
        commits = self.s.query(Commit).join((Script,
            Script.id==Commit.script_id)).filter(Script.id == \
                    script.id).order_by(desc(Commit.id)).offset(
                            _offset).limit(_limit).all()
        return commits

class CommitTool(object):

    def __init__(self, sess):
        self.s = sess

    def top(self, _offset=0, _limit=10):
        return self.s.query(Commit).order_by(desc(Commit.id)).offset(
            _offset).limit(_limit).all()

    def info(self, cid):
        return self.s.query(Commit).filter(Commit.id == cid).first()

    def add(self, user, script, time, vars):
        c = Commit(time)

        c.user = user
        c.script = script
        c.timeadd = time
        cv = []
        for x, y in vars.iteritems():
            commitvar = CommitVar(y)
            commitvar.commit = c
            commitvar.variable = x
            cv.append(commitvar)


        for v in cv:
            self.s.add(v)

        self.s.add(c)

        self.s.commit()

        return True

class VariableTool(object):

    def __init__(self, sess):
        self.s = sess

    def top(self, _offset=0, _limit=10, only_vars=False):
        obj = self.s.query(func.sum(CommitVar.amount), Variable).join(
                (Variable, Variable.id == CommitVar.variable_id))
        if only_vars:
            obj = obj.filter(Variable.is_var==1)
        obj = obj.group_by(Variable).order_by(desc('sum_1')).offset(
                         _offset).limit(_limit)
        return obj.all()

