from sqlalchemy import Table, Column, Integer, String, DateTime, func, \
     ForeignKey, Unicode

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()
metadata = Base.metadata

script_variables = Table('script_variables', metadata,
        Column('script_id', Integer, ForeignKey('scripts.id')),
        Column('variable_id', Integer, ForeignKey('variables.id'))
    )

class User(Base):
    """
        The User object represents a user.
        It has a name, password and date registered.
        Associated with the user are 'scripts' and 'commits'.

        Scripts consists of the scripts owned by the user,
        Commits consists of the commits submitted by the user.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(20), unique=True)
    password = Column(String(64), nullable=False)
    mail = Column(String(40), nullable=True)
    registertime = Column(DateTime, default=func.now())
    admin_level = Column(Integer, default=0)
    # scripts = user owned scripts
    # commits = user owned commits

    # rank
    rank = Column(Integer, default=0)

    def __init__(self, name, password, mail=None):
        self.name = name
        self.password = password
        self.mail = mail

    def __repr__(self):
        return 'User(%s)' % self.name.encode('utf8')

class Script(Base):
    """
        The Script object represents a script.
        It has a name, and an owner. The owner is a User instance.
    """
    __tablename__ = 'scripts'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(Unicode(40), unique=True)

    owner = relationship(User, backref=backref('scripts', order_by=id))
    variables = relationship('Variable', secondary=script_variables,
        backref='scripts')
    # commits = commits to script

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Script(%s : %s)' % (self.name, self.owner)

class Commit(Base):
    """
        The Commit object represents a single commit.
        A single commit consists of a user (User instance),
        a script (Script Instace), the time it adds and the time the
        commit has was submitted. Associated with a commit are additional
        variables. (Variable instances)
    """
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    script_id = Column(Integer, ForeignKey('scripts.id'))
    timeadd = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    user = relationship(User, backref=backref('commits', order_by=id))
    script = relationship(Script, backref=backref('commits', order_by=id))
    # commitvars = vars for this commit

    def __init__(self, timeadd):
        self.timeadd = timeadd

    def __repr__(self):
        return 'Commit(%d)' % self.id
        #return 'Commit(%s, %s, %s)' % (self.script,self.user,self.timeadd)


class Variable(Base):
    """
        The Variable object represents a Random Event or Script Variable.
        It has a name and a boolean to determine whether it is a variable
        or random event.
    """
    __tablename__ = 'variables'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(60), unique=True)

    # TODO -> turn to boolean?
    is_var = Column(Integer, nullable=False)
    # commitvars

    def __init__(self, name, is_var):
        self.name = name
        self.is_var = is_var

    def __repr__(self):
        return 'Variable(%s)' % (self.name)

class CommitVar(Base):
    """
        The CommitVar object represents a commit variable (value).
        It is linked to a specific Commit and Variable.
        It only holds an amount (of the specific variable)
    """
    __tablename__ = 'commitvars'

    id = None # Works?
    commit_id = Column(Integer, ForeignKey('commits.id'),primary_key=True)

    variable_id = Column(Integer, ForeignKey('variables.id'),primary_key=True)
    amount = Column(Integer, nullable=False)

    commit = relationship(Commit, backref=backref('commitvars', order_by=id))
    variable = relationship(Variable, backref=backref('commitvars', order_by=id))

    def __init__(self, amount):
        self.amount = amount
        pass

    def __repr__(self):
        return 'CommitVar(%s, %s, %s)' % (self.amount, self.commit,
                self.variable)

class UserScriptCache(Base):
    """
    """
    __tablename__ = 'uscache'

    id = None
    user_id = Column(Integer, ForeignKey('users.id'),primary_key=True)
    script_id = Column(Integer, ForeignKey('scripts.id'),primary_key=True)
    time_sum = Column(Integer)
    commit_amount = Column(Integer)

    user = relationship(User)
    script = relationship(Script)


    def __init__(self, user_id, script_id, time_sum, commit_amount):
        self.user_id = user_id
        self.script_id = script_id
        self.time_sum = time_sum
        self.commit_amount = commit_amount

    def __repr__(self):
        return 'USC(%s, %s, %d, %d)' % (self.user_id, self.script_id,
                self.time_sum, self.commit_amount)

class UserScriptVariableCache(Base): # Differs from UserScriptCache
    """
    """
    __tablename__ = 'usvcache'

    id = None
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    script_id = Column(Integer, ForeignKey('scripts.id'), primary_key=True)
    variable_id = Column(Integer, ForeignKey('variables.id'), primary_key=True)
    amount = Column(Integer)

    def __init__(self, user_id, script_id, variable_id, amount):
        self.user_id = user_id
        self.script_id = script_id
        self.variable_id = variable_id
        self.amount = amount

    def __repr__(self):
        return 'USVC(%s, %s, %s, %d)' % (self.user_id, self.script_id,
                self.variable_id, self.amount)
