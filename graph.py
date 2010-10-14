from cStringIO import StringIO

import matplotlib.pyplot as plt
from pylab import *
import numpy as np

class GraphTool(object):
    
    def __init__(self):
        pass

    def pie(self, frac, label, g_title, colours=None):
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
