#!/usr/bin/env python

from cli import *
from random import randrange

ul = session.query(User).all()
sl = session.query(Script).all()

# generate commits
for i in range(100):
    u = ul[randrange(0, len(ul))]
    s = sl[randrange(0, len(sl))]
    sv = s.variables
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

        session.add(cv)

    session.add(c)

session.commit()
