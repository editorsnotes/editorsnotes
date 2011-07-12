from urllib2 import urlopen
from lxml import etree
import re, json
from djotero.templatetags import interpret_json

NS = { 'xhtml': 'http://www.w3.org/1999/xhtml', 'zot' : "http://zotero.org/ns/api", 'atom' : "http://www.w3.org/2005/Atom" }

def request_permissions(zotero_uid, zotero_key):
    url = 'https://api.zotero.org/users/' + zotero_uid + '/groups?key=' + zotero_key
    xml_parse = etree.parse(urlopen(url))
    root = xml_parse.getroot()
    groups = root.xpath('./atom:entry', namespaces=NS)
    access = { 'zapi_version' : 'null', 'libraries' : [{'title' : 'Your Zotero library', 'location': 'https://api.zotero.org/users/' + zotero_uid }]}
    for x in groups:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        loc = x.xpath('./atom:link[@rel="self"]', namespaces=NS)[0].attrib['href']
        access['libraries'].append({'title' : title, 'location' : loc })
    return access

def list_collections(zotero_key, loc):
    url = loc + '/collections?key=' + zotero_key + '&limit=10&order=dateModified&format=atom&content=json'
    xml_parse = etree.parse(urlopen(url))
    root = xml_parse.getroot()
    entries = root.xpath('./atom:entry', namespaces=NS)
    collections = { 'zapi_version' : 'null', 'collections' : []}
    for x in entries:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        loc = x.xpath('./atom:link[@rel="self"]', namespaces=NS)[0].attrib['href']
        collections['collections'].append({ 'title' : title, 'location' : loc })
    return collections

def latest_items(zotero_key, loc):
    url = loc + '/items?key=' + zotero_key + '&limit=20&order=dateModified&format=atom&content=json'
    xml_parse = etree.parse(urlopen(url))
    root = xml_parse.getroot()
    entries = root.xpath('./atom:entry', namespaces=NS)
    latest = { 'zapi_version' : 'null', 'items' : []}
    for x in entries:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        library_url = x.xpath('./atom:id', namespaces=NS)[0].text
        item_id = x.xpath('./zot:key', namespaces=NS)[0].text
        item_json = x.xpath('./atom:content[@type="application/json"]', namespaces=NS)[0].text
        if json.loads(item_json)['itemType'] != 'note':
            item_csl = interpret_json.as_csl(item_json)
            latest['items'].append({'title' : title, 'loc' : loc, 'id' : item_id, 'url' : library_url, 'item_json' : item_json, 'item_csl' : item_csl })
    return latest
