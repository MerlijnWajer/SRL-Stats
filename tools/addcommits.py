#!/usr/bin/env python

import sys
sys.path.append('..')

from cli import *
from random import randrange

ul = Session.query(User).all()
sl = Session.query(Script).all()

# generate commits
for i in range(100):
    u = ul[randrange(0, len(ul))]
    s = sl[randrange(0, len(sl))]
    sv = s.variables + Session.query(Variable).filter(Variable.is_var==0).all()
    c = Commit(randrange(5, 30))
    c.script = s 
    c.user = u
    vu = []
    for j in range(len(sv)):
        v = sv[randrange(0,len(sv))]
        if v in vu:
            continue
        vu.append(v)
        cv = CommitVar(randrange(1,28))
        cv.commit = c
        cv.variable = v

        Session.add(cv)

    Session.add(c)

Session.commit()
