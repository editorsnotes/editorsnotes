import simplejson as json
from ordereddict import OrderedDict
from django.forms import Widget
from django.forms.util import flatatt
from django.utils.safestring import mark_safe
from utils import readable_map

class ZoteroWidget(Widget):
    """
    Render a zotero data string into a form.

    """
    def render(self, name, value, attrs=None):
        data = json.loads(value, object_pairs_hook=OrderedDict)
        html = '<br/><br/><br/><div id="zotero-information">'
        for key, val in data.items():

            wrapper_attrs = {'class' : 'zotero-entry',
                             'zotero-key' : key}
            item = ''

            if key == 'itemType':
                item += '<label>%s</label>' % key
                item += '<span zotero-item-type="%s">%s</span><br/><br/>' % (val, val)
            elif key == 'creators':
                creators = val
                if not creators:
                    pass
                for creator in creators:
                    creator_attrs = {}
                    creator_attrs['class'] = 'zotero-creator'
                    creator_attrs['creator-type'] = creator['creatorType']

                    creator_html = ''
                    creator_html += '<label>%s</label>&nbsp;' % creator['creatorType']
                    if creator.get('name'):
                        creator_html += '<textarea%s>%s</textarea>' % (
                            ' creator-key="name"', creator['name']
                        )
                    else:
                        creator_html += '<textarea%s>%s</textarea>, ' % (
                            ' creator-key="lastName"', creator['lastName']
                        )
                        creator_html += '<textarea%s>%s</textarea>' % (
                            ' creator-key="firstName"', creator['firstName']
                        )
                    item += '<span%s>%s</span><br/>' % (
                        flatatt(creator_attrs),creator_html
                    )
            elif key == 'tags':
                pass
            elif isinstance(val, unicode) :
                item += '<label>%s</label>&nbsp;' % (key)
                item += '<textarea%s>%s</textarea><br/>' % ('', val)

            if item:
                html += '<span%s>%s</span>' % (flatatt(wrapper_attrs), item)
        html += '</div>'
        return mark_safe(html)

    def get_creators(self):
        pass
