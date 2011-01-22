from cStringIO import StringIO

import matplotlib
matplotlib.use('svg')

import matplotlib.pyplot as plt
from pylab import *
import numpy as np

class GraphToolException(Exception):
    pass

def fig_to_data(fig):
    s = StringIO()
    fig.savefig(s)
    r = s.getvalue()
    s.close()
    return r


class GraphTool(object):
    
    def __init__(self):
        pass

    def commit_bar(self, _time, amount, _title='Unknown title', 
            _xlabel = 'Unknown time type', _ylabel='Unknown amount type'):
        """
            Generate a bar plot with <time> on X, amount on Y.
            Specify amount label with _ylabel, time label with _xlabel.
        """
        fig = plt.figure()

        h = fig.add_subplot(111)
        h.bar(_time, amount)

        plt.xlabel(_xlabel)
        plt.ylabel(_ylabel)
        plt.axis([_time[0], _time[len(_time)-1], 0, max(amount)])
        
        title(_title)

        return fig_to_data(fig)

    #def pie(self, frac, label, g_title, colours=None):
    #    if len(frac) != len(label):
    #        raise GraphToolException('len(frac) != len(label')

    #    fraclabel = self.normalise(zip(frac, label))

    #    frac, label = map(lambda x: x[0], fraclabel), map(lambda x: x[1],
    #            fraclabel)

    #    fig = plt.figure()

    #    p = fig.add_subplot(111)
    #    title(g_title)
    #    if colours is not None:
    #        p.pie(frac,labels=label,colors=colours)
    #    else:
    #        p.pie(frac,labels=label)

    #    s = StringIO()
    #    fig.savefig(s)
    #    r = s.getvalue()
    #    s.close()
    #    return r

    #def normalise(self, fraclabel):
    #    if len(fraclabel) < 15:
    #        return fraclabel

    #    fraclabel = sorted(fraclabel)
    #    fl = fraclabel[:14]
    #    _sum = sum(map(lambda x: x[0], fraclabel[14:]))
    #    fl.append((_sum, 'Others'))
    #    return fl


