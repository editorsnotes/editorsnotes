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
    url = 'https://api.zotero.org/' + loc + '/items?key=' + zotero_key + '&limit=10&order=dateModified&format=atom&content=none'
    xml_parse = etree.parse(urlopen(url))
    root = xml_parse.getroot()
    entries = root.xpath('./atom:entry', namespaces=NS)
    latest = { 'zapi_version' : 'null', 'items' : []}
    for x in entries:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        library_url = x.xpath('./atom:id', namespaces=NS)[0].text
        item_id = x.xpath('./zot:key', namespaces=NS)[0].text
        latest['items'].append({'title' : title, 'loc' : loc, 'id' : item_id, 'url' : library_url })
    return latest
