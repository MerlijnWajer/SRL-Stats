import sqlalchemy
from sqlalchemy import create_engine

try:
    from stats_credentials import dbu, dbpwd, dwh, dbp, dbname
except ImportError, e:
    print 'Cannot find stats_credentials!'

engine = create_engine("postgresql+psycopg2://%s:%s@%s:%s/%s" % (dbu, dbpwd,
    dwh, dbp, dbname))

# Pass echo=True to see all SQL queries
# When using MySQL; pass charset=utf8&use_unicode=1

from classes import User, Script, Variable, Commit, CommitVar, Base, \
    UserScriptCache, UserScriptVariableCache

Base.metadata.create_all(engine)
metadata = Base.metadata
from sqlalchemy.orm import scoped_session, sessionmaker
Session = scoped_session(sessionmaker(bind=engine))
