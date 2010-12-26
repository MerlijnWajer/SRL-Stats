#!/usr/bin/env python

import sys
sys.path.append('..')

from cli import *
from optparse import OptionParser

parse = OptionParser()
parse.add_option('-a', '--variable', dest='variables',
                help='Add variable',
                default=[], action='append', type=str)
parse.add_option('-r', '--random', dest='randoms',
                help='Add random (is_var=0)',
                default=[], action='append', type=str)
parse.add_option('-l', '--list', dest='list_vars',
                default=False, action='store_true')

o = parse.parse_args()[0]

if o.list_vars:
    vars = session.query(Variable).all()
    for x in vars:
        print x

    exit()

for var in o.variables:
    exists = session.query(Variable).filter(Variable.name == var).first()
    if exists is not None:
        print '%s already exists!' % var
        exit()

    v = Variable(var, 1)
    session.add(v)

for var in o.randoms:
    exists = session.query(Variable).filter(Variable.name == var).first()
    if exists is not None:
        print '%s already exists!' % var
        exit()

    v = Variable(var, 0)
    session.add(v)

session.commit()
