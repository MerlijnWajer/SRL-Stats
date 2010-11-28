#!/usr/bin/env python

from time import localtime
import gzip
from os import listdir
from time import time

# Logger class.
class PyLogger(object):
    # The three different log messages.
    INFO, WARNING, ERROR,\
            TIME, MESG = range(5)
    # TIME/MESG is merely here for the colour define
    # Green, Yellow, Red, Blue, Purple
    colours = map(lambda x: '\033[' + x + 'm', ['1;32', '1;33', '1;31', '1;34',
        '1;35'])

    # "\033[0m" == reset
    _msg = {INFO: '[II]', WARNING: '[WW]', ERROR : '[EE]'}
    _logfmt = '_type_ _time_ _mesg_'

    def colourise(self, s, t):
        return self.colours[t] + s + '\033[0m'

    def __init__(self):
        """
            Initialise a Logger instance.
            By default all logs are sent to stdout. It is possible to make
            Logger log to multiple files at the same time, by making log_to
            iterable.
        """

        # File descriptors and their data.
        self._fds = {}

    def __del__(self):
        """
            We should probably free files here.
        """
        for f in self._fds:
            del f

    def __getitem__(self, item):
        """
            Used to retrieve config for a specific file. Retreive files with
            get_logfiles().
        """
        if type(item) != file or not self._fds.has_key(item):
            raise InvalidFileDescriptorException(item)
        return self._fds[item]

    def __len__(self):
        """
            Return the amount of open files.
        """
        return len(self._fds)

    def assign_logfile(self, f, vlevel, outputs=(INFO, WARNING, ERROR),
            colour=True):
        """
            Add ``file'' to the the files that we write out logs to.
            If type(f) == file, then the file is added to the log list.
            If type(f) == str, then open file r/w and add to log list.
            level defines a verbosity level per file.
        """
        if type(f) is str:
            f = open(f, 'a+')

        if f in self._fds:
            raise FileAlreadyExistsException('%s already exists' % repr(f))

        self._fds[f] = {'level' : vlevel, 'outputs' : outputs, \
                'colour' : colour, 'time' : time()}
        return f

    def get_logfiles(self):
        """
            Return all log files in the files dict.
        """
        return self._fds.iterkeys()

    def set_log_fmt(self, logfmt):
        """
            Set the format for the log.
            _type_ is replaced with [II], [WW], [EE] depending on the type.
            _time_ is replaced with the current time.
            _mesg_ is replaced with the current message.
        """
        if type(logfmt) is not str:
            raise InvalidLogFormatException(logfmt)
        self._logfmt = logfmt

    def log(self, exclude, lvl, lt=INFO, *txts):
        """
            Log to all files that have a level less than or equal to lvl, and
            are not in exclude.
            fmt defines additional formats for the message. Defaults to
            currently set fmt.
        """
        fmt = self._logfmt
        for f, i in self._fds.iteritems():
            if f not in exclude and i['level'] >= lvl and lt in i['outputs']:
                txt = ''.join(map(lambda x: str(x) + ' ', txts))
                if i['colour']:
                    s = fmt.replace('_time_',
                            self.colourise(self._get_time(),PyLogger.TIME))\
                            .replace('_type_', self.colourise(self._msg[lt],\
                            lt)).replace('_mesg_', self.colourise(txt,
                                PyLogger.MESG))
                else:
                    s = fmt.replace('_time_', self._get_time()).\
                                replace('_type_', \
                            self._msg[lt],).replace('_mesg_', txt)
                self._internal_write(f, i, s, time() - i['time'] > 5)
        pass

    def _rotateFile(self, f, i):
        fn = f.name[:f.name.rfind('/')+1]
        ft = f.name[f.name.rfind('/')+1:]
        dl = sorted(filter(lambda x: x.startswith(ft + '.gz.'),
                listdir(fn)))
        if len(dl) == 0:
            rfn = fn + ft + '.gz.0'
        else:
            lf = dl[-1:][0]
            ln = int(lf[lf.rfind('.')+1:]) + 1
            rfn = fn + ft + '.gz.%s' % str(ln)

        f.seek(0)
        f_out = gzip.open(rfn, 'w')
        f_out.writelines(f)
        f_out.close()

        del self._fds[f]
        f.close()
        f = open(fn + ft, 'w+')
        self.assign_logfile(f, i['level'], i['outputs'])
        self[f]['rotate'] = i['rotate']

    def _internal_write(self, f, i, txt, vlus):
        f.write(txt + '\n')
        if vlus:
            f.flush()
            i['time'] = time()
        if i.has_key('rotate'):
            if f.tell() > i['rotate']:
                f.write('Rotating.\n')
                self._rotateFile(f, i)


    def _get_time(self):
        t = localtime()
        return '%02d-%02d %02d:%02d:%02d' % (t.tm_mon, t.tm_mday, t.tm_hour,
                t.tm_min, t.tm_sec)


class FileAlreadyExistsException(Exception):
    """
        Thrown when the file already exists in the FD dict.
    """
    pass

class InvalidLogFormatException(Exception):
    """
        Thrown when an invalid logformat is passed.
    """
    pass

class InvalidFileDescriptorException(Exception):
    """
        Thrown when an invalid File Description is passed.
    """
    pass

# Demonstration purposes only.
if __name__ == '__main__':
    from sys import stdout, stderr
    log = PyLogger()
    #log.set_log_fmt('_type_ _mesg_')
    #log.set_log_fmt('_type_ _time_ _mesg_')

    log.assign_logfile(stdout, 0, (PyLogger.WARNING, PyLogger.INFO))
    log.assign_logfile(stderr, 0, (PyLogger.ERROR,))
    ll = log.assign_logfile('/tmp/wat.log', 0)
    # In bytes
    log[ll]['rotate'] = 10000

    log[stdout]['colour'] = True
    for t, s in log._msg.iteritems():
        log.log([], 0, t, 'je moeder')
