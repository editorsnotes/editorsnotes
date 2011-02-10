# -*- coding: utf-8 -*-

import os.path
from lxml import etree
from pytz import timezone, utc
from django.conf import settings

textify = etree.XSLT(etree.parse(
        os.path.abspath(os.path.join(os.path.dirname(__file__), 'textify.xsl'))))

def xhtml_to_text(xhtml):
    if xhtml is None: 
        return ''
    string = etree.tostring(textify(xhtml), method='text', encoding=unicode)
    if string is None:
        return ''
    return string.strip()

def truncate(text, length=120):
    if len(text) <= length:
        return text
    l = text[:(length/2)].rsplit(' ', 1)[0]
    r = text[-(length/2):].split(' ', 1)
    if len(r) == 1:
        r = r[0]
    else:
        r = r[1]
    return l + u'... ' + r

def prepend_space(element):
    element.addprevious(etree.Entity('nbsp'))

def naive_to_utc(naive_datetime, timezone_string=None):
    '''Converts a naive datetime (such as Django returns from DateTimeFields) 
    to an timezone-aware UTC datetime. It will be assumed that the naive 
    datetime refers to a time in the timezone specified by settings.TIME_ZONE, 
    unless a timezone string (e.g. "America/Los_Angeles") is provided.'''
    if naive_datetime.tzinfo is not None:
        raise TypeError('datetime is not naive: %s' % naive_datetime)
    if timezone_string is None:
        timezone_string = settings.TIME_ZONE
    tz = timezone(timezone_string)
    return tz.normalize(tz.localize(naive_datetime)).astimezone(utc)
    
    
        
