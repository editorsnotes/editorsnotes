from urllib2 import urlopen
from lxml import etree
import re

NS = { 'xhtml': 'http://www.w3.org/1999/xhtml', 'zot' : "http://zotero.org/ns/api", 'atom' : "http://www.w3.org/2005/Atom" }

def request_permissions(zotero_uid, zotero_key):
    url = 'https://api.zotero.org/users/' + zotero_uid + '/groups?key=' + zotero_key
    xml_parse = etree.parse(urlopen(url))
    root = xml_parse.getroot()
    groups = root.xpath('./atom:entry', namespaces=NS)
    access = { 'zapi_version' : 'null', 'libraries' : [{'title' : 'Your Zotero library', 'type': 'users', 'id' : zotero_uid}]}
    for x in groups:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        idno = re.findall(r'/(\d*)$', x.xpath('./atom:id', namespaces=NS)[0].text)[0]
        access['libraries'].append({'title' : title, 'type' : 'groups', 'id' : idno})
    return access

def latest_items(zotero_key, loc):
    url = 'https://api.zotero.org/' + loc + '/items?key=' + zotero_key + '&limit=2&order=dateModified&format=atom&content=html'
    xml_parse = etree.parse(urlopen(url))
    root = xml_parse.getroot()
    entries = root.xpath('./atom:entry', namespaces=NS)
    latest = { 'zapi_version' : 'null', 'items' : []}
    for x in entries:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        url = x.xpath('./atom:id', namespaces=NS)[0].text
        #json_content = x.xpath('./atom:content', namespaces=NS)[0].text
        
        fields = x.xpath('./descendant::xhtml:tr', namespaces=NS)
        item_data = {}
        item_key = x.xpath('./zot:key', namespaces=NS)[0].text
        for y in fields:
            key = y.xpath('./xhtml:th', namespaces=NS)[0].text
            value = y.xpath('./xhtml:td', namespaces=NS)[0].text
            item_data[key] = value
        #latest['items'].append({'title' : title, 'key' : key, 'json_content': json_content})
        latest['items'].append({'title' : title, 'key' : item_key, 'data': item_data })
    return latest
