import simplejson as json
import re
from ordereddict import OrderedDict
from django.forms import Widget
from django.forms.util import flatatt
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from utils import type_map, contrib_map, field_map

field_help = {

    'archive' : '''In general, specify both an institution and specific 
collection. Start typing to see suggestions''',

    'archiveLocation' : '''Location within the archive described above. 
Examples: "Reel 7, frame 12", "Box 3", or "Scrapbook 7"''',

    'extra' : '''Any information that does not fit well in any other field'''

}

class ZoteroWidget(Widget):
    """
    Render a zotero data string into a form.

    """
    def render(self, name, value, attrs=None):

        ITEM_TYPE_SELECT = '<select id="zotero-item-type-select">%s</select>' % (
            '<option value=""></option>' +
            ''.join(['<option value="%s">%s</option>'% (
                item[0], item[1]) for item in type_map['readable'].items()]
            )
        )

        CREATOR_TYPE_SELECT = """
<select class="creator-select">
    <option value="%s">%s</option>
</select>
        """

        CREATOR_ADD_REMOVE = """
<a href="#_" class="creator-add">
    <img src="/django_admin_media/img/admin/icon_addlink.gif">
</a>
<a href="#_" class="creator-remove">
    <img src="/django_admin_media/img/admin/icon_deletelink.gif">
</a>
        """

        html = u'<div id="zotero-information"><br/><br/>'
        
        if not value:
            html += 'Add for item type: %s<br/>' % ITEM_TYPE_SELECT
            html += '</div>'
            return mark_safe(html)

        data = json.loads(force_unicode(value), object_pairs_hook=OrderedDict)
        key_counter = 0
        
        for key, val in data.items():

            item = ''
            itemAttrs = {'name' : 'zotero-key-%s|%s' % ("%02d" % key_counter, key )}

            if key == 'itemType':
                itemAttrs['type'] = 'hidden'
                itemAttrs['value'] = val
                item += """
<label>%s</label>
<input%s>
<span>%s&nbsp;</span>
<a href="#_" id="zotero-change-item-type">
    <img src="/django_admin_media/img/admin/icon_changelink.gif">
</a>
<div style="display: none" id="zotero-item-type-list">%s</div>
<br/><br/>
                """ % ('Item Type', flatatt(itemAttrs),
                       type_map['readable'][val], ITEM_TYPE_SELECT)

            elif key == 'creators':
                # Parse array of different creator objects which have the property
                # 'creatorType' as well as 1) name or 2) firstName and lastName
                creators = val
                itemAttrs['type'] = 'hidden'
                if not creators:
                    itemAttrs['value'] = '[]'
                    item += '<input%s>' % flatatt(itemAttrs)
                for creator in creators:

                    # Value to be posted is a json string inside a hidden
                    # input. If a creator is edited, this input must be updated
                    # with javascript.
                    itemAttrs['type'] = 'hidden'
                    itemAttrs['value'] = json.dumps(creator)
                    creator_input = '<input%s>' % flatatt(itemAttrs)

                    # Along with that hidden input, create nameless textareas
                    # for either a full name, or first + last name.
                    creator_attrs = {'class' : 'zotero-creator',
                                     'creator-type' : creator['creatorType']}
                    creator_html = ''
                    creator_selector = CREATOR_TYPE_SELECT % (
                        creator['creatorType'],
                        contrib_map['readable'][creator['creatorType']]
                    )
                    creator_html += '%s%s&nbsp;' % (
                        creator_selector, creator_input
                    )
                    if creator.get('name'):
                        creator_html += '<textarea%s>%s</textarea>' % (
                            ' class="creator-attr" creator-key="name"',
                            creator['name']
                        )
                    else:
                        creator_html += '<textarea%s>%s</textarea>, ' % (
                            ' class="creator-attr" creator-key="lastName"',
                            creator['lastName']
                        )
                        creator_html += '<textarea%s>%s</textarea>' % (
                            ' class="creator-attr" creator-key="firstName"',
                            creator['firstName']
                        )
                    item += '<span%s>%s%s<br/></span>' % (
                        flatatt(creator_attrs),creator_html, CREATOR_ADD_REMOVE
                    )

            elif key == 'tags':
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

            elif isinstance(val, unicode):
                if field_help.has_key(key):
                    itemAttrs['placeholder'] = field_help[key]
                item += '<label>%s</label>&nbsp;' % (field_map['readable'][key])
                item += '<textarea%s>%s</textarea><br/>' % (flatatt(itemAttrs), val)

            if item:
                wrapper_attrs = {'class' : 'zotero-entry', 'zotero-key' : key}
                html += '<span%s>%s</span>' % (flatatt(wrapper_attrs), item)
            key_counter += 1
        html += '</div>'
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        zotero_items = []
        key_finder = re.compile('zotero-key-(\d+)\|(.*)')
        for key, val in data.items():
            get_key = re.search(key_finder, key)
            if get_key:
                zotero_key = get_key.groups()
                zotero_items.append(
                    (zotero_key[0], zotero_key[1], data.getlist(key))
                )
        zotero_items.sort(key=lambda field: field[0])
        zotero_dict = OrderedDict()
        for item in zotero_items:
            zotero_key = item[1]
            if zotero_key == 'creators':
                zotero_data = [json.loads(creator) for creator in item[2] if creator != u'[]']
            elif zotero_key == 'tags':
                zotero_data = [json.loads(tag) for tag in item[2] if tag != u'[]']
            else:
                zotero_data = item[2][0]
            zotero_dict[zotero_key] = zotero_data

        # Don't return a dict if there's not enough data (something more than
        # just itemType)
        validation = [val for val in zotero_dict.values()
                      if isinstance(val, unicode) and val]
        if len(validation) > 1:
            return json.dumps(zotero_dict)
        else:
            return None
