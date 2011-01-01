# Find exact depends?
from sqlalchemy import *
from classes import User, Script, Variable, Commit, CommitVar, Base

class StatsTool(object):
    def __init__(self, sell):
        """
            We need a SQLAlchemy session.
        """
        self.s = sell

class UserTool(StatsTool):
    """
        UserTool is a User helper class. It doesn't have to be OOP; and OOP
        may be dropped later on depending whether I still plan to make a 
        caching mechanism or not.
    """

    def top(self, _offset=0,_limit=10):
        """
            Return the top *limit* users based on time added.
        """
        return self.s.query(User, func.coalesce(func.sum(Commit.timeadd),
            literal_column('0'))).outerjoin(
            (Commit, Commit.user_id == User.id)).group_by(
             User).order_by(desc('coalesce_1')).offset(
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

        restime = {'commit_amount' : int(time[0]), 'commit_time' : int(time[1])
                if time[1] is not None else 0}

        return dict(zip(['user', 'time'], [user, restime]))

    def info_script(self, uid, sid):
        """
            Returns the user object, script object, time statistics and
            variables commits by the user with their amount.
        """
        user = self.s.query(User).filter(User.id == uid).first()
        if user is None:
            return None

        script = self.s.query(Script).filter(Script.id == sid).first()
        if script is None:
            return None

        time = self.s.query(func.count(Commit.timeadd),
                func.sum(Commit.timeadd)).filter(Commit.user_id == uid).filter(
                        Commit.script_id == sid).first()

        vars = self.s.query(func.sum(CommitVar.amount), Variable.name).join(
            (Variable, CommitVar.variable_id == Variable.id)).join(
            (Commit, Commit.id == CommitVar.commit_id)).filter(Commit.user_id ==
                uid).filter(Commit.script_id == sid).group_by(Variable.name).all()

        my_vars = [(int(x[0]), x[1]) for x in vars]

        restime = {'commit_amount' : int(time[0]), 'commit_time' : int(time[1])
                if time[1] is not None else 0}

        return dict(zip(['user', 'script', 'vars', 'time'], [user, script, \
                my_vars, restime]))
        
    def listc_script(self, uid, sid, _offset=0, _limit=10):
        """
            Return the commits made by user to a specific script.
        """
        user = self.s.query(User).filter(User.id == uid).first()
        if user is None:
            return None

        script = self.s.query(Script).filter(Script.id == sid).first()
        if script is None:
            return None

        commits = self.s.query(Commit).join(
            (User, User.id==Commit.user_id)).filter(
                User.id == uid).filter(
                Commit.script_id == sid).order_by(
                desc(Commit.id)).offset(
                _offset).limit(_limit).all()

        return dict(user=user, script=script,commits=commits)

    def listc(self, user, _offset=0, _limit=10):
        """
            Return the commits made by user.
        """
        commits = self.s.query(Commit).join((User,
            User.id==Commit.user_id)).filter(User.id == \
                    user.id).order_by(desc(Commit.id)).offset(
                    _offset).limit(_limit).all()
        return commits

class ScriptTool(StatsTool):

    def top(self, _offset=0, _limit=10):
        return self.s.query(Script.name, Script.id, func.coalesce(
            func.sum(Commit.timeadd), literal_column('0'))).outerjoin(
                (Commit, Commit.script_id == Script.id)).group_by(
             Script.name, Script.id).order_by(desc('coalesce_1')).offset(
                     _offset).limit(_limit).all()

    def info(self, sid):
        script = self.s.query(Script).filter(Script.id==sid).first()
        if script is None:
            return None

        vars = self.s.query(func.sum(CommitVar.amount), Variable).join(
                (Variable, CommitVar.variable_id==Variable.id)).join(
                (Commit, Commit.id == CommitVar.commit_id)).filter(
                 Commit.script_id == sid).group_by(Variable).all()

        my_vars = [(int(x[0]), x[1]) for x in vars]

        time = self.s.query(func.count(Commit.timeadd), 
                func.sum(Commit.timeadd)).join(
                (Script, Commit.script_id == Script.id)).filter(
                Script.id == sid).first()

        restime = {'commit_amount' : int(time[0]), 'commit_time' : int(time[1]) if time[1]
                is not None else 0}

        return dict(zip(['script', 'vars', 'time'], [script, my_vars, restime]))

    def listc(self, script, _offset=0, _limit=10):
        commits = self.s.query(Commit).join((Script,
            Script.id==Commit.script_id)).filter(Script.id == \
                    script.id).order_by(desc(Commit.id)).offset(
                            _offset).limit(_limit).all()
        return commits

class CommitTool(StatsTool):

    def top(self, _offset=0, _limit=10):
        return self.s.query(Commit).order_by(desc(Commit.id)).offset(
            _offset).limit(_limit).all()

    def info(self, cid):
        return self.s.query(Commit).filter(Commit.id == cid).first()

    def add(self, user, script, time, vars):
        """
            Add a commit to the system.
        """
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
        # XXX: Failsafe?

        return True

class VariableTool(StatsTool):

    def top(self, _offset=0, _limit=10, only_vars=False):
        obj = self.s.query(Variable, func.coalesce(func.sum(CommitVar.amount),
            literal_column('0'))).outerjoin(
                (CommitVar, Variable.id == CommitVar.variable_id))
        if only_vars:
            obj = obj.filter(Variable.is_var==1)
        obj = obj.group_by(Variable).order_by(desc('coalesce_1')).offset(
                         _offset).limit(_limit)
        return obj.all()

    def info(self, variableid):
        variable = \
            self.s.query(Variable).filter(Variable.id==variableid).first()
        if variable is None:
            return None

        amount = self.s.query(func.sum(CommitVar.amount)).filter(
                    CommitVar.variable_id==variableid).first()

        return dict(zip(['variable', 'amount'], [variable, amount]))
