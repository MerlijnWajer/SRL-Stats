import re
# Regex rules to call the right stuff on the right url.
# May eventually turn it all into one regex? Would make it less readable
# though.

# XXX: TODO: Integers hard limited at 8 chars max. Python has unlimited
# integers; but databases do not. If someone passes 999999999999999999
# then we will get a database error. This ``fix'' works around it.
# Until you get more than 999999 users.

# Typically 10 digits would suffice, as we reach the max somewhere in the 11
# digits.

# User rules
wt.add_rule(re.compile('^%s/user/([0-9]{1,8})$' % BASE_URL),
        user, ['userid'])

wt.add_rule(re.compile('^%s/user/([0-9]{1,8})/commits$' \
        % BASE_URL), user_commit, ['userid'])

wt.add_rule(re.compile('^%s/user/([0-9]{1,8})/commits/([0-9]{1,8})?$' \
        % BASE_URL), user_commit, ['userid', 'pageid'])

wt.add_rule(re.compile('^%s/user/([0-9]{1,8})/script/([0-9]{1,8})$' \
        % BASE_URL), user_script_stats, ['userid', 'scriptid'])

wt.add_rule(re.compile(
    '^%s/user/([0-9]{1,8})/script/([0-9]{1,8})/commits/([0-9]{1,8})?$' \
        % BASE_URL), user_script_commits, ['userid', 'scriptid', 'pageid'])

# Two rules. We don't want to match /user/all10
wt.add_rule(re.compile('^%s/user/all/?$' % BASE_URL),
        users, [])

wt.add_rule(re.compile('^%s/user/all/([0-9]{1,8})?$' % BASE_URL),
        users, ['pageid'])

# Script rules

wt.add_rule(re.compile('^%s/script/([0-9]{1,8})$' % BASE_URL),
        script, ['scriptid'])

wt.add_rule(re.compile('^%s/script/([0-9]{1,8})/commits$' \
        % BASE_URL), script_commit, ['scriptid'])

wt.add_rule(re.compile('^%s/script/([0-9]{1,8})/commits/([0-9]{1,8})?$' \
        % BASE_URL), script_commit, ['scriptid', 'pageid'])

wt.add_rule(re.compile('^%s/script/all/?$' % BASE_URL),
        scripts, [])

wt.add_rule(re.compile('^%s/script/all/([0-9]{1,8})?$' % BASE_URL),
        scripts, ['pageid'])

# Commit rules
wt.add_rule(re.compile('^%s/commit/([0-9]{1,8})$' % BASE_URL),
        commit, ['commitid'])

wt.add_rule(re.compile('^%s/commit/all/?$' % BASE_URL),
        commits, [])

wt.add_rule(re.compile('^%s/commit/all/([0-9]{1,8})?$' % BASE_URL),
        commits, ['pageid'])

# Variable rules
wt.add_rule(re.compile('^%s/variable/([0-9]{1,8})$' % BASE_URL),
        variable, ['variableid'])

wt.add_rule(re.compile('^%s/variable/all/?$' % BASE_URL),
        variables, [])

wt.add_rule(re.compile('^%s/variable/all/([0-9]{1,8})?$' % BASE_URL),
        variables, ['pageid'])

# Login rules
wt.add_rule(re.compile('^%s/login$' % BASE_URL), login, [])

wt.add_rule(re.compile('^%s/logout$' % BASE_URL), logout, [])

wt.add_rule(re.compile('^%s/register$' % BASE_URL), register_user, [])

# API
wt.add_rule(re.compile('^%s/api/commit$' % BASE_URL), api_commit, [])

wt.add_rule(re.compile('^%s/api/script/([0-9]{1,8})$' % BASE_URL),
    signature_api_script, ['scriptid'])

wt.add_rule(re.compile('^%s/api/user/([0-9]{1,8})$' % BASE_URL),
    signature_api_user, ['userid'])

wt.add_rule(re.compile('^%s/api/commit/last$' % BASE_URL),
        signature_api_commit, [])

# Manage rules

wt.add_rule(re.compile('^%s/manage/scripts$' % BASE_URL), manage_scripts, [])
wt.add_rule(re.compile('^%s/manage/script/([0-9]{1,8})$' % BASE_URL),
    manage_script, ['scriptid'])
wt.add_rule(re.compile('^%s/manage/script/new$' % BASE_URL), create_script, [])

wt.add_rule(re.compile('^%s/manage/variable/new$' % BASE_URL), create_variable, [])
wt.add_rule(re.compile('^%s/manage/variable/([0-9]{1,8})$' % BASE_URL),
    manage_variable, ['variableid'])
wt.add_rule(re.compile('^%s/manage/variables/([0-9]{1,8})?$' % BASE_URL),
        manage_variables, ['pageid'])

wt.add_rule(re.compile('^%s/script/([0-9]{1,8})/graph$' % BASE_URL),
        script_graph, ['scriptid'])

wt.add_rule(re.compile('^%s/graph/commits(?:/month/([0-9]{1,8}))?(?:/year/'\
        '([0-9]{1,8}))?(?:/script/([0-9]{1,8}))?(?:/user/([0-9]{1,8}))'\
        '?(?:/type/([A-z]+))?$' % BASE_URL),
        graph_commits, ['month', 'year', 'scriptid', 'userid', 'select_type' ])

wt.add_rule(re.compile('^%s/graph/commits_year((?:/year/'\
        '([0-9]{1,8}))?(?:/script/([0-9]{1,8}))?(?:/user/([0-9]{1,8}))'\
        '?(?:/type/([A-z]+))?$' % BASE_URL),
        graph_commits, ['month', 'year', 'scriptid', 'userid', 'select_type' ])

wt.add_rule(re.compile('^%s/robots.txt$' % BASE_URL), robots, [])

# Default page
wt.add_rule(re.compile('^%s/?$' % BASE_URL), general, [])
