#!/usr/bin/python
# -*- coding: utf-8 -*-
# Python example
# http://jasminsms.com
#https://groups.google.com/g/jasmin-sms-gateway/c/tv1IeQo1KKc/m/UWTWCb-t_EAJ
#Mozete pouzit data_coding 0 pre GSM03.38,4 pre 8-bit binary, 8 pre UCS2.

import urllib2
import urllib
import binascii
import sys

reload(sys)
sys.setdefaultencoding('utf8')

baseParams = {'username':'omid', 'password':'omid@123', 'to':'+989212371918', 'content':'', 'from':'6715'}

# Sending UCS2 (UTF-16) arabic content
baseParams['content'] = '12345678901234567890123456789012345678901234567890'.encode('utf-16-be')
baseParams['coding'] = 8
print urllib2.urlopen("http://127.0.0.1:1401/send?%s" % urllib.urlencode(baseParams)).read()