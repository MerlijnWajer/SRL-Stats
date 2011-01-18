#!/usr/bin/env python

import hashlib

import sys
sys.path.append('..')

from cli import *

# directory of ukwords
w = [x.replace('\n', '') for x in open('../ukwords_small')]

essence = Variable(u'Essence', 1)
coal = Variable(u'Coal', 1)
iron = Variable(u'Iron', 1)
oak = Variable(u'Oak', 1)
yew = Variable(u'Yew', 1)
tuna = Variable(u'Tuna', 1)
salmon = Variable(u'Salmon', 1)

Session.add(essence)
Session.add(coal)
Session.add(iron)
Session.add(oak)
Session.add(yew)
Session.add(tuna)
Session.add(salmon)

s1 = Script(u'Essence Miner')
s2 = Script(u'Iron Miner')
s3 = Script(u'Fisher')
s4 = Script(u'Woodcutter')
s5 = Script(u'Edgeville Yew Cutter')
s6 = Script(u'Lumbridge Coal / Iron Miner')

s1.variables.append(essence)
s2.variables.append(iron)
s3.variables.append(tuna)
s3.variables.append(salmon)
s4.variables.append(oak)
s4.variables.append(yew)
s5.variables.append(yew)
s6.variables.append(iron)
s6.variables.append(coal)

Session.add(s1)
Session.add(s2)
Session.add(s3)
Session.add(s4)
Session.add(s5)
Session.add(s6)

for i in range(100):
    u = User(w[i], unicode(hashlib.sha256(w[i]).hexdigest()))
    Session.add(u)

ul = Session.query(User).all()

from random import randrange
s1.owner = ul[randrange(0,99)]
s2.owner = ul[randrange(0,99)]
s3.owner = ul[randrange(0,99)]
s4.owner = ul[randrange(0,99)]
s5.owner = ul[randrange(0,99)]
s6.owner = ul[randrange(0,99)]

Session.commit()
