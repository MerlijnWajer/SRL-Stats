# Find exact depends?
from sqlalchemy import *
from classes import User, Script, Variable, Commit, CommitVar, Base

class UserTool(object):

    def __init__(self, sess):
        self.s = sess
        pass

    def top(self, limit):
        return self.s.query(func.sum(Commit.timeadd), User.name).join(
            (User, Commit.user_id == User.id)).group_by(
             User.name).order_by(desc('sum_1')).limit(limit)
    
    def info(self, id):
        user = self.s.query(User).filter(User.id==id).first()
        time = self.s.query(func.count(Commit.timeadd), 
                func.sum(Commit.timeadd)).join(
                (User, Commit.user_id == User.id)).filter(
                User.id == id).first()

        return dict(zip(['user', 'time'], [user, time]))

