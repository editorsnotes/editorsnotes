import json
import re
from collections import OrderedDict
from django.forms import Widget
from django.forms.util import flatatt
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from utils import type_map, contrib_map, field_map, get_creator_types
import re

field_help = {

    'archive' : '''In general, specify both an institution and a collection. 
Start typing to see suggestions''',

    'archiveLocation' : '''Location within the archive described above. 
Examples: "Reel 7, frame 12", "Box 3", or "Scrapbook 7"''',

    'extra' : '''Any information that does not fit well in another field'''

}

class ZoteroWidget(Widget):
    """
    Render a zotero data string into a form.

    If given an empty string, the widget will render as a select field with
    options for different item types.

    To preserve field order, a zotero data dict is rendered into separate
    fields, given a counter and a label, like 'zotero-key-01-itemType'. Values
    for the hidden creator inputs must be updated by javascript if edited.
    """
    def render(self, name, value, attrs=None):

        def wrap_control_group(key, val, field, classes=[]):
            attrs = {}
            attrs['class'] = ' '.join(classes + ['zotero-entry', 'control-group'])
            attrs['data-zotero-key'] = key
            control_html = ('<div %s>' % flatatt(attrs) +
                                '<label class="control-label">%s</label>' % val +
                                '<div class="controls">' + field + '</div>' +
                            '</div>')
            return mark_safe(control_html)

        html = u'<div id="zotero-information-edit">'

        ITEM_TYPES = ''.join([ '<option value="%s">%s</option>' % (key, val)
                               for key, val in type_map['readable'].items() ])
        ITEM_TYPE_SELECT = ('<select name="item-type-select">' +
                                '<option value=""></option>' +
                                ITEM_TYPES + '</select>')

        CREATOR_ADD_REMOVE = ('&nbsp;<i class="add-creator icon-plus-sign"></i>' +
                              '<i class="remove-creator icon-minus-sign"></i>')

        if not value:
            html += ('<div id="item-type-select-dialog" class="control-group">' +
                     '<label class="control-label">Item Type</label>' +
                     '<div class="controls">%s</div>' % ITEM_TYPE_SELECT)
            return mark_safe(html)

        data = json.loads(force_unicode(value), object_pairs_hook=OrderedDict)
        key_counter = 0
        
        for key, val in data.items():
            input_attrs = {'name': 'zotero-key-%02d-%s' % (key_counter, key)}

            if key == 'itemType':
                input_attrs['type'] = 'hidden'
                input_attrs['value'] = val

                field = ('<label><strong>%s</strong></label>' % type_map['readable'][val] +
                         '<input %s />' % flatatt(input_attrs))
                html += wrap_control_group('itemType', 'Item type', field)

            elif key == 'creators':
                # Parse array of different creator objects which have the property
                # 'creatorType' as well as 1) name or 2) firstName and lastName
                creators = val
                input_attrs['type'] = 'hidden'

                try:
                    creator_types = json.loads(get_creator_types(data['itemType']))
                except:
                    creator_types = []

                if not creators:
                    continue

                for creator in creators:
                    # Value to be posted is a json string inside a hidden
                    # input. If a creator is edited, this input must be updated
                    # with javascript.
                    field = ''
                    ctype = creator['creatorType']

                    creator_type_options = (
                        '\n'.join([ '<option %svalue="%s">%s</option>' % (
                            'selected="selected"' if c['creatorType'] == ctype else '',
                            c['creatorType'],
                            c['localized']) for c in creator_types ]))
                    creator_type_options = (
                        creator_type_options or '<option value="%s">%s</option>' % (
                        ctype, contrib_map['readable'][ctype]))
                    creator_select = ('<select data-creator-key="creatorType" class="creator-select creator-attr">' +
                                      creator_type_options + '</select>')

                    input_attrs['value'] = json.dumps(creator)
                    field += '<input%s>' % flatatt(input_attrs)

                    if creator.get('name'):
                        field += '<textarea%s>%s</textarea>' % (
                            flatatt({'class': 'creator-attr',
                                     'data-creator-key': 'name'}),
                            creator['name'])
                    else:
                        field += '<textarea%s>%s</textarea>' % (
                            flatatt({'class': 'creator-attr',
                                     'data-creator-key': 'lastName'}),
                            creator['lastName'])
                        field += ', '
                        field += '<textarea%s>%s</textarea>' % (
                            flatatt({'class': 'creator-attr',
                                     'data-creator-key': 'firstName'}),
                            creator['firstName'])
                    field += CREATOR_ADD_REMOVE
                    html += wrap_control_group(
                        'creators', creator_select, field,
                        classes=['zotero-creator'])

            elif key == 'tags':
                continue
                tags = val
                itemAttrs['type'] = 'hidden'
                if not tags:
                    itemAttrs['value'] = '[]'
                    item += '<input%s>' % flatatt(itemAttrs)
                for tag in tags:
                    # Like the creator field, this must also be updated with
                    # javascript.
                    itemAttrs['value'] = json.dumps(tag)
                    item += '<input%s>' % flatatt(itemAttrs) 

            elif isinstance(val, basestring):
                if field_help.has_key(key):
                    input_attrs['placeholder'] = field_help[key]
                field = '<textarea%s>%s</textarea>' % (flatatt(input_attrs), val)
                html += wrap_control_group(
                    key, field_map['readable'][key], field)

            key_counter += 1

        html += ('<div class="control-group zotero-entry-delete">' +
                 '<label class="control-label">Delete metadata?</label>' +
                 '<div class="controls">' +
                    '<input type="checkbox" name="zotero-data-DELETE" value="DELETE" />' +
                 '</div></div>')

        html += '</div>'
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):

        if data.has_key('zotero_data'):
            # This allows us to render this widget from a json string that's not
            # split into different fields. This is necessary so that we can
            # render this widget from something other than an existing object--
            # especially a blank form.
            return force_unicode(data['zotero_data'])

        zotero_items = []
        key_finder = re.compile('zotero-key-(\d+)-(.*)')
        for key, val in data.items():
            get_key = re.search(key_finder, key)
            if get_key:
                zotero_key = get_key.groups()
                zotero_items.append(
                    (zotero_key[0], zotero_key[1], data.getlist(key)))
        zotero_items.sort(key=lambda field: field[0])
        zotero_dict = OrderedDict()
        for counter, zotero_key, zotero_val_list in zotero_items:
            if zotero_key == 'creators':
                zotero_val = [json.loads(creator) for creator in zotero_val_list]
            elif zotero_key == 'tags':
                zotero_val = [json.loads(tag) for tag in zotero_val_list]
            else:
                (zotero_val,) = zotero_val_list
            zotero_dict[zotero_key] = zotero_val

        # Don't return a dict if there's not enough data (something more than
        # just itemType)
        populated_fields = [val for val in zotero_dict.values()
                      if isinstance(val, basestring) and val]
        if len(populated_fields) <= 1:
            return None

        return json.dumps(zotero_dict)
