from cStringIO import StringIO

import matplotlib
matplotlib.use('svg')

import matplotlib.pyplot as plt
from pylab import *
import numpy as np

class GraphToolException(Exception):
    pass

class GraphTool(object):
    
    def __init__(self):
        pass

    def pie(self, frac, label, g_title, colours=None):
        if len(frac) != len(label):
            raise GraphToolException('len(frac) != len(label')

        fraclabel = self.normalise(zip(frac, label))

        frac, label = map(lambda x: x[0], fraclabel), map(lambda x: x[1],
                fraclabel)

        fig = plt.figure()

        p = fig.add_subplot(111)
        title(g_title)
        if colours is not None:
            p.pie(frac,labels=label,colors=colours)
        else:
            p.pie(frac,labels=label)

        s = StringIO()
        fig.savefig(s)
        r = s.getvalue()
        s.close()
        return r

    def normalise(self, fraclabel):
        if len(fraclabel) < 15:
            return fraclabel

        fraclabel = sorted(fraclabel)
        fl = fraclabel[:14]
        _sum = sum(map(lambda x: x[0], fraclabel[14:]))
        fl.append((_sum, 'Others'))
        return fl
