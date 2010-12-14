import re
# Regex rules to call the right stuff on the right url.
# May eventually turn it all into one regex? Would make it less readable
# though.

# XXX: TODO: Integers hard limited at 6 chars max. Python has unlimited
# integers; but databases do not. If someone passes 999999999999999999
# then we will get a database error. This ``fix'' works around it.
# Until you get more than 999999 users.

# User rules
wt.add_rule(re.compile('^%s/user/([0-9]{1,6})$' % BASE_URL),
        user, ['userid'])

wt.add_rule(re.compile('^%s/user/([0-9]{1,6})/commits$' \
        % BASE_URL), user_commit, ['userid'])

wt.add_rule(re.compile('^%s/user/([0-9]{1,6})/commits/([0-9]{1,6})?$' \
        % BASE_URL), user_commit, ['userid', 'pageid'])

# Two rules. We don't want to match /user/all10
wt.add_rule(re.compile('^%s/user/all/?$' % BASE_URL),
        users, [])

wt.add_rule(re.compile('^%s/user/all/([0-9]{1,6})?$' % BASE_URL),
        users, ['pageid'])

# Script rules

wt.add_rule(re.compile('^%s/script/([0-9]{1,6})$' % BASE_URL),
        script, ['scriptid'])

wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/commits$' \
        % BASE_URL), script_commit, ['scriptid'])

wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/commits/([0-9]{1,6})?$' \
        % BASE_URL), script_commit, ['scriptid', 'pageid'])

wt.add_rule(re.compile('^%s/script/([0-9]{1,6})/graph$' % BASE_URL),
        script_graph, ['scriptid'])

wt.add_rule(re.compile('^%s/script/all/?$' % BASE_URL),
        scripts, [])

wt.add_rule(re.compile('^%s/script/all/([0-9]{1,6})?$' % BASE_URL),
        scripts, ['pageid'])

# Commit rules
wt.add_rule(re.compile('^%s/commit/([0-9]{1,6})$' % BASE_URL),
        commit, ['commitid'])

wt.add_rule(re.compile('^%s/commit/all/?$' % BASE_URL),
        commits, [])

wt.add_rule(re.compile('^%s/commit/all/([0-9]{1,6})?$' % BASE_URL),
        commits, ['pageid'])

# Variable rules
wt.add_rule(re.compile('^%s/variable/([0-9]{1,6})$' % BASE_URL),
        variable, ['variableid'])

wt.add_rule(re.compile('^%s/variable/all/?$' % BASE_URL),
        variables, [])

wt.add_rule(re.compile('^%s/variable/all/([0-9]{1,6})?$' % BASE_URL),
        variables, ['pageid'])

# Login rules
wt.add_rule(re.compile('^%s/login$' % BASE_URL), login, [])

wt.add_rule(re.compile('^%s/logout$' % BASE_URL), logout, [])

wt.add_rule(re.compile('^%s/api/commit$' % BASE_URL), api_commit, [])

wt.add_rule(re.compile('^%s/api/si/([0-9]{1-6})$' % BASE_URL),
        api_scriptinfo, [])

wt.add_rule(re.compile('^%s/api/ui/([0-9]{1-6})$' % BASE_URL),
        api_userinfo, [])

wt.add_rule(re.compile('^%s/manage/scripts$' % BASE_URL), manage_scripts, [])
wt.add_rule(re.compile('^%s/manage/script/([0-9]{1-6})$' % BASE_URL),
    manage_script, ['scriptid'])


# Default page
wt.add_rule(re.compile('^%s/?$' % BASE_URL),
            general, [])

# One rule to rule them all...
# ^%s/(user|script|commit)/all/?([0-9]{1,6}?/?$
