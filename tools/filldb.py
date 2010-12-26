#!/usr/bin/env python

from cli import *

# directory of ukwords
w = [x.replace('\n', '') for x in open('../ukwords_small')]

essence = Variable('Essence', 1)
coal = Variable('Coal', 1)
iron = Variable('Iron', 1)
oak = Variable('Oak', 1)
yew = Variable('Yew', 1)
tuna = Variable('Tuna', 1)
salmon = Variable('Salmon', 1)

session.add(essence)
session.add(coal)
session.add(iron)
session.add(oak)
session.add(yew)
session.add(tuna)
session.add(salmon)

s1 = Script('Essence Miner')
s2 = Script('Iron Miner')
s3 = Script('Fisher')
s4 = Script('Woodcutter')
s5 = Script('Edgeville Yew Cutter')
s6 = Script('Lumbridge Coal / Iron Miner')

s1.variables.append(essence)
s2.variables.append(iron)
s3.variables.append(tuna)
s3.variables.append(salmon)
s4.variables.append(oak)
s4.variables.append(yew)
s5.variables.append(yew)
s6.variables.append(iron)
s6.variables.append(coal)

session.add(s1)
session.add(s2)
session.add(s3)
session.add(s4)
session.add(s5)
session.add(s6)

for i in range(100):
    u = User(w[i], w[i])
    session.add(u)

ul = session.query(User).all()

from random import randrange
s1.owner = ul[randrange(0,99)]
s2.owner = ul[randrange(0,99)]
s3.owner = ul[randrange(0,99)]
s4.owner = ul[randrange(0,99)]
s5.owner = ul[randrange(0,99)]
s6.owner = ul[randrange(0,99)]

session.commit()
