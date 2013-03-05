# -*- coding: utf-8 -*-

import os.path
import re
import unicodedata
from lxml import etree
from pytz import timezone, utc
from django.conf import settings
from django.utils.encoding import smart_text

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

def alpha_columns(items, sortattr, num_columns=3, itemkey='item'):
    items = list(items)
    sortkey = lambda item: getattr(item, sortattr)
    items.sort(key=sortkey)
    prev_letter = 'A'
    item_index = 0
    column_index = 0 
    columns = [[] for i in range(3)]
    for item in items:
        first_letter = sortkey(item)[0].upper()
        if not first_letter == prev_letter:
            if (column_index < num_columns and 
                item_index > (len(items) / float(num_columns))):
                item_index = 0
                column_index += 1
            prev_letter = first_letter
        columns[column_index].append(
            { itemkey: item, 'first_letter': first_letter })
        item_index += 1
    return columns

def unicode_slugify(s):
    """Return a unicode slug for the given string

    Adapted from Mozilla's unicode-slugify. License included below."""
    slug_chars = []
    string = smart_text(s).strip().rstrip()
    for char in unicodedata.normalize('NFKC', string):
        category = unicodedata.category(char)[0]
        if category in 'LN' or char in '_,-':
            slug_chars.append(char)
        elif category == 'Z':
            slug_chars.append('_')
    slug = ''.join(slug_chars)
    slug = re.sub(r'([_,\-])\1+', r'\1', slug)
    return slug

# unicode-slugify 0.1
#
# Copyright (c) 2011, Mozilla Foundation
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
# 
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
# 
#     3. Neither the name of unicode-slugify nor the names of its contributors
#        may be used to endorse or promote products derived from this software
#        without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
