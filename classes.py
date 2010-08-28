from sqlalchemy import Table, Column, Integer, String, DateTime, func, \
     ForeignKey

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()
metadata = Base.metadata

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True)
    password = Column(String(32), nullable=False)
    registertime = Column(DateTime, default=func.now())
    # scripts = user owned scripts
    # commits = user owned commits
    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return '<User(%s)>' % self.name

class Script(Base):
    __tablename__ = 'scripts'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(40), unique=True)

    owner = relationship(User, backref=backref('scripts', order_by=id))
    # commits = commits to script

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Script(%s : %s)>' % (self.name, self.owner)

class Commit(Base):
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
        return '<Commit(%s, %s, %s)>' % (self.script,self.user,self.timeadd)


class Variable(Base):
    __tablename__ = 'variables'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)

    # TODO -> turn to boolean?
    is_var = Column(Integer, nullable=False)
    # commitvars

    def __init__(self, name, is_var):
        self.name = name
        self.is_var = is_var

class CommitVar(Base):
    __tablename__ = 'commitvars'

    id = None # Works?
    commit_id = Column(Integer, ForeignKey('commits.id'),primary_key=True)
    random_id = Column(Integer, ForeignKey('variables.id'),primary_key=True)
    amount = Column(Integer, nullable=False)

    commit = relationship(Commit, backref=backref('commitvars', order_by=id))
    variable = relationship(Variable, backref=backref('commitvars', order_by=id))

    def __init__(self, amount):
        self.amount = amount
        pass

