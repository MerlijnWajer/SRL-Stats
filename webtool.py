#!/usr/bin/env python

# REQUEST_METHOD = GET/POST
# REQUEST_URI = /mai/linkoe
# IP = REMOTE_ADDR

class WebToolException(Exception):
    """
        Raised on an exception in the WebTool.
    """

class WebTool(object):
    """
        The WebTool class provides me with the required MiddleWare utilities.
        Current functionality:
            -   URL-Based function calling and argument parsing.
    """

    def __init__(self):
        self.rules = {}
        pass

    def add_rule(self, rule, func, varnames):
        """
            Add a new rule. The rule has to be a regex object. (Use re.compile)
            func is called with varnames amount of named arguments.
        """
        if rule in self.rules:
            raise WebToolException('Rule %s already exists' % rule)
        self.rules[rule] = {'func': func, 'vars': varnames}

    def add_rules(self, rules, funcs, varnames):
        for rule, func, vnames in zip(rules, funcs, varnames):
            self.add_rule(rule, func, vnames)
    
    def apply_rule(self, url):
        """
            apply_rule finds an appropriate rule and applies it if found.
        """
        for rule, fv in self.rules.iteritems():
            m = rule.match(url)
            if m:
                l = [x for x in m.groups()]
                if len(l) != len(fv['vars']):
                    raise WebToolException('Matches does not equal variable \
                            amount')
                return fv['func'](**dict(zip(fv['vars'], l)))
        return None

def prt(userid=None):
    print userid, scriptid

if __name__ == '__main__':
    import re
    w = WebTool()
    w.add_rule(re.compile('^/stats/user/([0-9]+)$'), prt, ['userid'])
    print w.apply_rule('/stats/user/42')
