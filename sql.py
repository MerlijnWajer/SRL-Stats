import sqlalchemy
from sqlalchemy import create_engine
engine = create_engine('sqlite:///database.db', echo=True)

from classes import User, Script, Variable, Commit, CommitVar, Base

Base.metadata.create_all(engine)
metadata = Base.metadata
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()
