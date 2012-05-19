from sql import User, Script, Variable, Commit, CommitVar, \
        UserScriptCache, UserScriptVariableCache, Base, Session
from sqlalchemy import func
from sqlalchemy import extract

def update_user_script_cache():
    """
    """
    print 'Updating user-script cache...'
    session = Session()

    update_query = str(session.query(User.id, Script.id,
        func.sum(Commit.timeadd), func.count(Commit.id)
        ).join((Commit, Commit.user_id==User.id)).join(
            (Script, Script.id == Commit.script_id)).group_by(
            User.id, Script.id))

    session.execute('TRUNCATE TABLE uscache') # CASCADE?
    session.execute('INSERT INTO uscache %s' % update_query)
    session.commit()

    del session
    print 'Done updating user-script cache...'

def update_user_script_variable_cache():
    """
    """
    print 'Updating user-script-variable cache...'
    session = Session()

    update_query = str(session.query(User.id, Script.id, Variable.id,
        func.sum(CommitVar.amount)).join(
            (Commit, Commit.user_id == User.id)).join(
            (Script, Commit.script_id == Script.id)).join(
            (CommitVar, CommitVar.commit_id == Commit.id)).join(
            (Variable, Variable.id == CommitVar.variable_id)).group_by(
            User.id, Script.id, Variable.id))

    session.execute('TRUNCATE TABLE usvcache') # CASCADE?
    session.execute('INSERT INTO usvcache %s' % update_query)
    session.commit()

    del session
    print 'Done updating user-script-variable cache...'

if __name__ == '__main__':
        update_user_script_cache()
        update_user_script_variable_cache()

