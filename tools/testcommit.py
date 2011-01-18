import urllib
import urllib2

import hashlib

url = 'http://localhost/stats/api/commit'
#url = 'http://old.villavu.com/stats/api/commit'
values = {
            'user' : 'whines',
            'password' : '',
            'script' : '1',
            'essence' : '28',
            'time' : '5'
        }

data = urllib.urlencode(values)
print data
req = urllib2.Request(url, data)
response = urllib2.urlopen(req)
the_page = response.read()
print the_page
