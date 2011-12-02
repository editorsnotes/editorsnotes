import simplejson as json
from ordereddict import OrderedDict
from django.forms import Widget
from django.utils.safestring import mark_safe

class ZoteroWidget(Widget):
    """
    Render a zotero data string into a form.

    """
    def render(self, name, value, attrs=None):
        def pair_to_html(key, val):
            field = """
<span class="zotero-key">%s:&nbsp;</span>
<textarea rows="1" cols="60" class="zotero-val" name="%s">%s</textarea><br/>
            """ % (key, key, val)
            return field
        def creators_to_html(creators):
            creator_count = 1
            field = ''
            add_or_remove = """
<span class="creator-add creator-button"><img
src="/django_admin_media/img/admin/icon_addlink.gif"></span>
<span class="creator-remove creator-button"><img
src="/django_admin_media/img/admin/icon_deletelink.gif"></span><br/>
            """
            for creator in creators:
                c = dict(creator)
                field += '<span class="zotero-key">%s&nbsp;</span>' % c['creatorType']
                if c.get('name'):
                    name_field = """
<textarea class="zotero-val" name="creator-%s-name">%s</textarea><br/>
                    """ % ( str(creator_count),
                            c.get('name') )
                else:
                    name_field = """
<textarea class="zotero-val" name="creator-%s-lastName">%s</textarea>, 
<textarea class="zotero-val" name="creator-%s-firstName">%s</textarea>
                    """ % ( str(creator_count),
                            c.get('lastName'),
                            str(creator_count),
                            c.get('firstName') )
                field += name_field
                field += add_or_remove
            return field
        data = json.loads(value, object_pairs_hook=OrderedDict)
        html = '<br/><br/><div id="zotero-data">'
        skip_fields = ['itemType', 'url']
        for key, val in data.items():
            if isinstance(val, unicode) and key not in skip_fields:
                html += pair_to_html(key, val)
            elif isinstance(val, list):
                if key == 'creators':
                    html += creators_to_html(val)
            else:
                pass
        html += '</form>'
        return mark_safe(html)
