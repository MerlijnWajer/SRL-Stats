"""
    Query.py consists out of several useful classes to work with the User,
    Script, Variable, Commit and CommitVar classes.
"""
# Find exact depends?
from sqlalchemy import *
from classes import User, Script, Variable, Commit, CommitVar, \
    UserScriptCache, UserScriptVariableCache

class StatsTool(object):
    def __init__(self, sess):
        """
            We need a SQLAlchemy session.
        """
        self.s = sess

class UserTool(StatsTool):
    """
        UserTool is a User helper class. It doesn't have to be OOP; and OOP
        may be dropped later on depending whether I still plan to make a
        caching mechanism or not.
    """

    def top(self, _offset=0,_limit=10, cache=False):
        """
            Return the top *limit* users based on time added.
        """

        if cache:
            coales = (func.coalesce(func.sum(UserScriptCache.time_sum), \
                literal_column('0'))).label('TimeAdd')
            obj = self.s.query(User, coales).outerjoin(
                    (UserScriptCache, UserScriptCache.user_id == User.id))
        else:
            coales = (func.coalesce(func.sum(Commit.timeadd), \
                literal_column('0'))).label('TimeAdd')
            obj = self.s.query(User, coales).outerjoin(
                (Commit, Commit.user_id == User.id))

        obj = obj.group_by(User)
        obj = obj.order_by(desc(coales),asc(User.id))
        obj = obj.offset(_offset)

        if _limit > 0:
            obj = obj.limit(_limit)

        return obj.all()

    def info(self, uid, cache=False):
        """
            Returns the user object with id *uid* and the time and commit count
            of the user.
        """
        user = self.s.query(User).filter(User.id==uid).first()
        if user is None:
            return None

        if cache:
            time = self.s.query(func.sum(UserScriptCache.commit_amount),
                    func.sum(UserScriptCache.time_sum)).filter(
                UserScriptCache.user_id == uid).group_by(UserScriptCache.user_id).first()

            vars = self.s.query(func.sum(UserScriptVariableCache.amount),
                    Variable).join((Variable, Variable.id ==
                    UserScriptVariableCache.variable_id)).filter(
                    UserScriptVariableCache.user_id == uid).group_by(
                    Variable).all()
        else:
            time = self.s.query(func.count(Commit.timeadd),
                func.sum(Commit.timeadd)).join(
                (User, Commit.user_id == User.id)).filter(
                User.id == uid).first()

            vars = self.s.query(func.sum(CommitVar.amount), Variable).join(
                    (Variable, CommitVar.variable_id == Variable.id)).join(
                    (Commit, Commit.id == CommitVar.commit_id)).filter(
                    Commit.user_id == uid).group_by(Variable).all()

        my_vars = [(int(x[0]), x[1]) for x in vars]

        restime = \
            {'commit_amount' : 0, 'commit_time' : 0} if time is None else \
            {'commit_amount' : int(time[0]) if time[0] is not None else 0,
             'commit_time' : int(time[1]) if time[1] is not None else 0}

        return dict(zip(['user', 'time', 'vars'], [user, restime, my_vars]))

    def info_script(self, uid, sid, cache=False):
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

        if cache:
            time = self.s.query(UserScriptCache.commit_amount,
                    UserScriptCache.time_sum).filter(UserScriptCache.user_id == uid).filter(
                    UserScriptCache.script_id == sid).first()

            vars = self.s.query(func.sum(UserScriptVariableCache.amount),
                   Variable.name).join((Variable, Variable.id == \
                   UserScriptVariableCache.variable_id)).filter(
                   UserScriptVariableCache.user_id == uid).filter(
                   UserScriptVariableCache.script_id == sid).group_by(
                   Variable.name).all()
        else:
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
            Returns the user object as *user*; the script as *script* and the
            commits as *commits*.
        """
        # Make sure the user exists.
        user = self.s.query(User).filter(User.id == uid).first()
        if user is None:
            return None

        # Make sure the script exists.
        script = self.s.query(Script).filter(Script.id == sid).first()
        if script is None:
            return None

        # Get all the commits.
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
    """
        ScriptTool is a Script helper. It can return the top scripts and return
        script specific information; such as vars and time. It can also list the
        commits made to a script.
    """

    def top(self, _offset=0, _limit=10, cache=False):
        """
            Return the top scripts; based on the time committed to the script.
        """

        if cache:
            coales = (func.coalesce(func.sum(UserScriptCache.time_sum), \
                    literal_column('0'))).label('TimeAdd')
            obj = self.s.query(Script.name, Script.id, coales).outerjoin(
                    (UserScriptCache, UserScriptCache.script_id == Script.id))
        else:
            coales = (func.coalesce(func.sum(Commit.timeadd), \
                    literal_column('0'))).label('TimeAdd')
            obj = self.s.query(Script.name, Script.id, coales).outerjoin(
                    (Commit, Commit.script_id == Script.id))

        obj = obj.group_by(Script.name, Script.id)
        obj = obj.order_by(desc(coales),asc(Script.id))
        obj = obj.offset(_offset)

        if _limit > 0:
            obj = obj.limit(_limit)

        return obj.all()

    def info(self, sid, cache=False):
        """
            Return script information:
                -   Script Object
                -   Variables *committed* to the script
                -   Time committed to the script (the amount of commits and
                    their total time)
        """
        script = self.s.query(Script).filter(Script.id==sid).first()
        if script is None:
            return None

        if cache:
            vars = self.s.query(func.sum(UserScriptVariableCache.amount),
                Variable).join((Variable, UserScriptVariableCache.variable_id \
                == Variable.id)).filter(UserScriptVariableCache.script_id \
                == sid).group_by(Variable).all()
                # Why do I need to group by all the Variable entities? XXX
        else:
            vars = self.s.query(func.sum(CommitVar.amount), Variable).join(
                (Variable, CommitVar.variable_id==Variable.id)).join(
                (Commit, Commit.id == CommitVar.commit_id)).filter(
                 Commit.script_id == sid).group_by(Variable).all()

        my_vars = [(int(x[0]), x[1]) for x in vars]

        if cache:
            time = self.s.query(func.sum(UserScriptCache.commit_amount),
                func.sum(UserScriptCache.time_sum)).filter(
                UserScriptCache.script_id == sid).first()
        else:
            time = self.s.query(func.count(Commit.timeadd),
                func.sum(Commit.timeadd)).join(
                (Script, Commit.script_id == Script.id)).filter(
                Script.id == sid).first()

        restime = {'commit_amount' : int(time[0] if time[0] is not None else 0),
                   'commit_time' : int(time[1]) if time[1] is not None else 0}

        return dict(zip(['script', 'vars', 'time'], [script, my_vars, restime]))

    def listc(self, script, _offset=0, _limit=10):
        """
            List the commits of the script.
        """
        commits = self.s.query(Commit).join((Script,
            Script.id==Commit.script_id)).filter(Script.id == \
                    script.id).order_by(desc(Commit.id)).offset(
                            _offset).limit(_limit).all()
        return commits

class CommitTool(StatsTool):
    """
        CommitTool is a Commit helper. It can add a commit; return the top
        commits (latest) and return commit specific information.
    """

    def top(self, _offset=0, _limit=10):
        """
            Return the newest commits (ordered by the time they were added, or
            rather; by their id; descending.
        """
        obj = self.s.query(Commit).order_by(desc(Commit.id)).offset(
            _offset)
        if _limit > 0:
            obj = obj.limit(_limit)

        return obj.all()

    def info(self, cid):
        """
            Return commit object of the commit with id *cid*.
        """
        return self.s.query(Commit).filter(Commit.id == cid).first()

    def add(self, user, script, time, vars):
        """
            Add a commit to the system.
        """

        session = self.s()

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
            session.add(v)

        session.add(c)

        try:
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            print 'Rollback in query.py; ct.add! ... ', user, script, time, vars
            print 'Data:', user, script, time, vars
            print 'Exception:', e

        return True

class VariableTool(StatsTool):
    """
        VariableTool is the Variable helper. It can return the top variables
        based on the amount the variable has been committed; it can also return
        variable specific information.
    """

    def top(self, _offset=0, _limit=10, only_vars=False, cache=False):
        """
            Return the top Variables.
        """

        if cache:
            coales = (func.coalesce(func.sum(UserScriptVariableCache.amount), \
                literal_column('0'))).label('AmountSum')
            obj = self.s.query(Variable, coales).outerjoin(
                    (UserScriptVariableCache,
                     UserScriptVariableCache.variable_id == Variable.id))
        else:
            coales = (func.coalesce(func.sum(CommitVar.amount), \
                literal_column('0'))).label('AmountSum')
            obj = self.s.query(Variable, coales).outerjoin(
                (CommitVar, Variable.id == CommitVar.variable_id))

        if only_vars:
            obj = obj.filter(Variable.is_var==1)

        obj = obj.group_by(Variable).order_by(desc(coales),
            asc(Variable.id)).offset(_offset)

        if _limit > 0:
            obj = obj.limit(_limit)

        return obj.all()

    def info(self, variableid, cache=False):
        """
            Return information about the variable: The total commit amount plus
            the Variable object.
        """
        variable = \
            self.s.query(Variable).filter(Variable.id==variableid).first()
        if variable is None:
            return None

        if cache:
            amount = self.s.query(func.sum(UserScriptVariableCache.amount)
                ).filter(UserScriptVariableCache.variable_id == variableid
                ).group_by(UserScriptVariableCache.variable_id).first()
        else:
            amount = self.s.query(func.sum(CommitVar.amount)).filter(
                    CommitVar.variable_id==variableid).first()

        return dict(zip(['variable', 'amount'], [variable, amount]))
