from cStringIO import StringIO

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

class GraphToolException(Exception):
    pass

def fig_to_data(fig):
    s = StringIO()
    fig.print_png(s)
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
        fig = Figure(edgecolor='#FFFFFF', facecolor='#FFFFFF')
        canvas = FigureCanvas(fig)

        h = fig.add_subplot(111)
        h.bar(_time, amount)

        h.set_xlabel(_xlabel)
        h.set_ylabel(_ylabel)
        h.set_xbound(_time[0], _time[len(_time)-1])
        h.set_ybound(0, int(max(amount)))
        h.set_axis_bgcolor('#FFFFFF')

        h.set_title(_title)

        return fig_to_data(canvas)
