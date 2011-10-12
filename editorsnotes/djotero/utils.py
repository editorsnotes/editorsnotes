from urllib2 import urlopen
from lxml import etree
import re, json

NS = {'xhtml': 'http://www.w3.org/1999/xhtml',
      'zot' : "http://zotero.org/ns/api",
      'atom' : "http://www.w3.org/2005/Atom"}

# Zotero API calls
def libraries(zotero_uid, zotero_key):
    url = 'https://api.zotero.org/users/%s/groups?key=%s' % (zotero_uid, zotero_key)
    access = {'zapi_version' : 'null',
              'libraries' : [{'title' : 'Your Zotero library',
                              'location': 'https://api.zotero.org/users/%s' % zotero_uid }]}
    for x in parse_xml(url):
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        loc = x.xpath('./atom:link[@rel="self"]', namespaces=NS)[0].attrib['href']
        access['libraries'].append({'title' : title, 'location' : loc })
    return access

def collections(zotero_key, loc):
    url = '%s/collections?key=%s&limit=10&order=dateModified&format=atom&content=json' % (loc, zotero_key)
    collections = { 'zapi_version' : 'null',
                    'collections' : []}
    for x in parse_xml(url):
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        loc = x.xpath('./atom:link[@rel="self"]', namespaces=NS)[0].attrib['href']
        collections['collections'].append({ 'title' : title, 'location' : loc })
    return collections

def items(zotero_key, loc):
    url = loc + '/items?key=' + zotero_key + '&limit=20&order=dateModified&format=atom&content=json'
    latest = { 'zapi_version' : 'null', 'items' : []}
    for x in parse_xml(url):
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        library_url = x.xpath('./atom:id', namespaces=NS)[0].text
        item_id = x.xpath('./zot:key', namespaces=NS)[0].text
        item_json = x.xpath('./atom:content[@type="application/json"]', namespaces=NS)[0].text
        try:
            item_date = json.loads(item_json)['date']
        except:
            item_date = ""
        if json.loads(item_json)['itemType'] not in ['note', 'attachment']:
            citeproc_identifier = library_url[library_url.rindex('items') + 6:]
            item_csl = as_csl(item_json, citeproc_identifier)
            latest['items'].append(
                {'title' : title,
                 'loc' : loc,
                 'id' : item_id,
                 'date' : item_date,
                 'url' : library_url,
                 'item_json' : item_json,
                 'item_csl' : item_csl })
    return latest

# Helper functions
def as_csl(zotero_json_string, citeproc_identifier):
    zotero_data = json.loads(zotero_json_string)
    genre = zotero_data['itemType']
    field_translation = csl_map[genre]
    output = {}
    for old, new in field_translation.items():
        if zotero_data[old]:
            output[new] = zotero_data[old]
    if zotero_data['creators']:
        names = resolve_names(zotero_data, 'csl')
        for contrib_type in names.keys():
            output[contrib_type] = names[contrib_type]
    output['type'] = type_map['csl'][genre]
    output['id'] = citeproc_identifier # For use with citeproc-js.
    try:
        if zotero_data['date']:
            output['issued'] = { 'raw' : zotero_data['date'] }
    except KeyError:
        if zotero_data['dateDecided']:
            output['issued'] = { 'raw' : zotero_data['dateDecided'] }
    return json.dumps(output)

def as_readable(zotero_json_string):
    zotero_data_list = []
    content = json.loads(zotero_json_string)
    content.pop('tags')
    content['itemType'] = type_map['readable'][content['itemType']]
    if content['creators']:
        names = resolve_names(content, 'readable')
        for name in names:
            zotero_data_list.append(name)
        content.pop('creators')
    for x in content.keys():
        if content[x]:
            zotero_data_list.append({'type' : x, 'label' : readable_map[x]['name'], 'value' : content[x], 'display_category' : readable_map[x]['category']})
    return zotero_data_list

def resolve_names(zotero_data, format):
    if format == 'csl':
        # CSl output requires a dictionary whose keys are each creator type.
        # The values of these keys are lists containing individual dictionaries
        # containing the parts of each contributors' name. Example:
        #
        #{ 'author' : [{ "family" : "Doe", "given" : "Jane"},
        #              { "family" : "Doe", "given" : "John"}],
        #  'recipient' : [etc]}
        contribs = {}
        for creator in zotero_data['creators']:
            try:
                name = { "family" : creator['lastName'], "given" : creator['firstName'] }
            except:
                name = { "literal" : creator['name'] }
            contribs.setdefault(contrib_map['csl'][creator['creatorType']], []).append(name)

    if format == 'facets':
        # Data to be used in facets only needs a sortable name, either 'lastName' or 'name'
        contribs = []
        for creator in zotero_data['creators']:
            try:
                name = creator['lastName']
            except:
                name = creator['name']
            contribs.append({creator['creatorType'] : name})
        
    if format == 'readable':
        contribs = []
        for creator in zotero_data['creators']:
            try:
                name = creator['firstName'] + ' ' + creator['lastName']
            except:
                name = creator['name']
            contribs.append({'type' : creator['creatorType'], 'label' : contrib_map['readable'][creator['creatorType']], 'value' : name, 'display_category' : 3})
    
    return contribs

def parse_xml(url):
    xml_parse = etree.parse(urlopen(url))
    root = xml_parse.getroot()
    return root.xpath('./atom:entry', namespaces=NS)

# Map to translate JSON from Zotero to something understandable by citeproc-js CSL engine.
# See http://gsl-nagoya-u.net/http/pub/csl-fields/
csl_map = {
    "artwork": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "artworkMedium": "medium", 
        "artworkSize": "genre", 
        "callNumber": "call-number", 
        "extra": "note", 
        "title": "title", 
        "url": "URL"
    }, 
    "audioRecording": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "audioRecordingFormat": "medium", 
        "callNumber": "call-number", 
        "extra": "note", 
        "label": "publisher", 
        "numberOfVolumes": "number-of-volumes", 
        "place": "publisher-place", 
        "seriesTitle": "collection-title", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "bill": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "billNumber": "number", 
        "code": "container-title", 
        "codePages": "page", 
        "codeVolume": "volume", 
        "extra": "note", 
        "history": "references", 
        "section": "section", 
        "title": "title", 
        "url": "URL"
    }, 
    "blogPost": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "blogTitle": "container-title", 
        "extra": "note", 
        "title": "title", 
        "url": "URL", 
        "websiteType": "genre"
    }, 
    "book": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "edition": "edition", 
        "extra": "note", 
        "numPages": "number-of-pages", 
        "numberOfVolumes": "number-of-volumes", 
        "place": "publisher-place", 
        "publisher": "publisher", 
        "series": "collection-title", 
        "seriesNumber": "collection-number", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "bookSection": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "bookTitle": "container-title", 
        "callNumber": "call-number", 
        "edition": "edition", 
        "extra": "note", 
        "numberOfVolumes": "number-of-volumes", 
        "pages": "page", 
        "place": "publisher-place", 
        "publisher": "publisher", 
        "series": "collection-title", 
        "seriesNumber": "collection-number", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "case": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "caseName": "title", 
        "court": "authority", 
        "dateDecided": "issued", 
        "docketNumber": "number", 
        "extra": "note", 
        "firstPage": "page", 
        "history": "references", 
        "reporter": "container-title", 
        "reporterVolume": "volume", 
        "url": "URL"
    }, 
    "computerProgram": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "company": "publisher", 
        "extra": "note", 
        "place": "publisher-place", 
        "seriesTitle": "collection-title", 
        "title": "title", 
        "url": "URL", 
        "version": "version"
    }, 
    "conferencePaper": {
        "DOI": "DOI", 
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "conferenceName": "event", 
        "extra": "note", 
        "pages": "page", 
        "place": "publisher-place", 
        "proceedingsTitle": "container-title", 
        "publisher": "publisher", 
        "series": "collection-title", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "dictionaryEntry": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "dictionaryTitle": "container-title", 
        "edition": "edition", 
        "extra": "note", 
        "numberOfVolumes": "number-of-volumes", 
        "pages": "page", 
        "place": "publisher-place", 
        "publisher": "publisher", 
        "series": "collection-title", 
        "seriesNumber": "collection-number", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "document": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "extra": "extra", 
        "language": "language", 
        "publisher": "publisher", 
        "rights": "rights", 
        "title": "title", 
        "url": "URL"
    }, 
    "email": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "extra": "note", 
        "subject": "title", 
        "url": "URL"
    }, 
    "encyclopediaArticle": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "edition": "edition", 
        "encyclopediaTitle": "container-title", 
        "extra": "note", 
        "numberOfVolumes": "number-of-volumes", 
        "pages": "page", 
        "place": "publisher-place", 
        "publisher": "publisher", 
        "series": "collection-title", 
        "seriesNumber": "collection-number", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "film": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "distributor": "publisher", 
        "extra": "note", 
        "genre": "genre", 
        "title": "title", 
        "url": "URL", 
        "videoRecordingFormat": "medium"
    }, 
    "forumPost": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "extra": "note", 
        "forumTitle": "container-title", 
        "postType": "genre", 
        "title": "title", 
        "url": "URL"
    }, 
    "hearing": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "documentNumber": "number", 
        "extra": "note", 
        "history": "references", 
        "numberOfVolumes": "number-of-volumes", 
        "pages": "page", 
        "place": "publisher-place", 
        "publisher": "publisher", 
        "title": "title", 
        "url": "URL"
    }, 
    "instantMessage": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "extra": "note", 
        "title": "title", 
        "url": "URL"
    }, 
    "interview": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "interviewMedium": "medium", 
        "title": "title", 
        "url": "URL"
    }, 
    "journalArticle": {
        "DOI": "DOI", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "issue": "issue", 
        "pages": "page", 
        "publicationTitle": "container-title", 
        "series": "collection-title", 
        "seriesTitle": "collection-title", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "letter": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "letterType": "genre", 
        "title": "title", 
        "url": "URL"
    }, 
    "magazineArticle": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "issue": "issue", 
        "pages": "page", 
        "publicationTitle": "container-title", 
        "title": "title", 
        "url": "URL", 
        "volume": "volume"
    }, 
    "manuscript": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "manuscriptType": "genre", 
        "numPages": "number-of-pages", 
        "place": "publisher-place", 
        "title": "title", 
        "url": "URL"
    }, 
    "map": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "edition": "edition", 
        "extra": "note", 
        "mapType": "genre", 
        "place": "publisher-place", 
        "publisher": "publisher", 
        "seriesTitle": "collection-title", 
        "title": "title", 
        "url": "URL"
    }, 
    "newspaperArticle": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "edition": "edition", 
        "extra": "note", 
        "pages": "page", 
        "place": "publisher-place", 
        "publicationTitle": "container-title", 
        "section": "section", 
        "title": "title", 
        "url": "URL"
    }, 
    "patent": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "extra": "note", 
        "issueDate": "issued", 
        "pages": "page", 
        "patentNumber": "number", 
        "place": "publisher-place", 
        "references": "references", 
        "title": "title", 
        "url": "URL"
    }, 
    "podcast": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "audioFileType": "medium", 
        "episodeNumber": "number", 
        "extra": "note", 
        "seriesTitle": "collection-title", 
        "title": "title", 
        "url": "URL"
    }, 
    "presentation": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "extra": "note", 
        "meetingName": "event", 
        "place": "publisher-place", 
        "presentationType": "genre", 
        "title": "title", 
        "url": "URL"
    }, 
    "radioBroadcast": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "audioRecordingFormat": "medium", 
        "callNumber": "call-number", 
        "episodeNumber": "number", 
        "extra": "note", 
        "network": "publisher", 
        "place": "publisher-place", 
        "programTitle": "container-title", 
        "title": "title", 
        "url": "URL"
    }, 
    "report": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "institution": "publisher", 
        "pages": "page", 
        "place": "publisher-place", 
        "reportNumber": "number", 
        "reportType": "genre", 
        "seriesTitle": "collection-title", 
        "title": "title", 
        "url": "URL"
    }, 
    "statute": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "code": "container-title", 
        "dateEnacted": "issued", 
        "extra": "note", 
        "history": "references", 
        "nameOfAct": "title", 
        "pages": "page", 
        "publicLawNumber": "number", 
        "section": "section", 
        "url": "URL"
    }, 
    "thesis": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "numPages": "number-of-pages", 
        "place": "publisher-place", 
        "thesisType": "genre", 
        "title": "title", 
        "university": "publisher", 
        "url": "URL"
    }, 
    "tvBroadcast": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "episodeNumber": "number", 
        "extra": "note", 
        "network": "publisher", 
        "place": "publisher-place", 
        "programTitle": "container-title", 
        "title": "title", 
        "url": "URL", 
        "videoRecordingFormat": "medium"
    }, 
    "videoRecording": {
        "ISBN": "ISBN", 
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "archive": "archive", 
        "archiveLocation": "archive_location", 
        "callNumber": "call-number", 
        "extra": "note", 
        "numberOfVolumes": "number-of-volumes", 
        "place": "publisher-place", 
        "seriesTitle": "collection-title", 
        "studio": "publisher", 
        "title": "title", 
        "url": "URL", 
        "videoRecordingFormat": "medium", 
        "volume": "volume"
    }, 
    "webpage": {
        "abstractNote": "abstract", 
        "accessDate": "accessed", 
        "extra": "note", 
        "title": "title", 
        "url": "URL", 
        "websiteTitle": "container-title", 
        "websiteType": "genre"
    }
}

readable_map = {
    'DOI': {'category': 7, 'name': 'DOI'},
    'ISBN': {'category': 7, 'name': 'ISBN'},
    'ISSN': {'category': 7, 'name': 'ISSN'},
    'abstractNote': {'category': 7, 'name': 'Abstract'},
    'accessDate': {'category': 4, 'name': 'Accessed'},
    'applicationNumber': {'category': 7, 'name': 'Application Number'},
    'archive': {'category': 5, 'name': 'Archive'},
    'archiveLocation': {'category': 5, 'name': 'Loc. in Archive'},
    'artworkMedium': {'category': 7, 'name': 'Medium'},
    'artworkSize': {'category': 7, 'name': 'Artwork Size'},
    'assignee': {'category': 7, 'name': 'Assignee'},
    'audioFileType': {'category': 7, 'name': 'File Type'},
    'audioRecordingFormat': {'category': 7, 'name': 'Format'},
    'billNumber': {'category': 7, 'name': 'Bill Number'},
    'blogTitle': {'category': 5, 'name': 'Blog Title'},
    'bookTitle': {'category': 5, 'name': 'Book Title'},
    'callNumber': {'category': 6, 'name': 'Call Number'},
    'caseName': {'category': 7, 'name': 'Case Name'},
    'code': {'category': 7, 'name': 'Code'},
    'codeNumber': {'category': 7, 'name': 'Code Number'},
    'codePages': {'category': 7, 'name': 'Code Pages'},
    'codeVolume': {'category': 7, 'name': 'Code Volume'},
    'committee': {'category': 7, 'name': 'Committee'},
    'company': {'category': 7, 'name': 'Company'},
    'conferenceName': {'category': 7, 'name': 'Conference Name'},
    'country': {'category': 7, 'name': 'Country'},
    'court': {'category': 7, 'name': 'Court'},
    'date': {'category': 4, 'name': 'Date'},
    'dateDecided': {'category': 4, 'name': 'Date Decided'},
    'dateEnacted': {'category': 4, 'name': 'Date Enacted'},
    'dictionaryTitle': {'category': 5, 'name': 'Dictionary Title'},
    'distributor': {'category': 7, 'name': 'Distributor'},
    'docketNumber': {'category': 7, 'name': 'Docket Number'},
    'documentNumber': {'category': 7, 'name': 'Document Number'},
    'edition': {'category': 5, 'name': 'Edition'},
    'encyclopediaTitle': {'category': 5, 'name': 'Encyclopedia Title'},
    'episodeNumber': {'category': 7, 'name': 'Episode Number'},
    'extra': {'category': 7, 'name': 'Extra'},
    'filingDate': {'category': 7, 'name': 'Filing Date'},
    'firstPage': {'category': 7, 'name': 'First Page'},
    'forumTitle': {'category': 5, 'name': 'Forum/Listserv Title'},
    'genre': {'category': 7, 'name': 'Genre'},
    'history': {'category': 7, 'name': 'History'},
    'institution': {'category': 7, 'name': 'Institution'},
    'interviewMedium': {'category': 7, 'name': 'Medium'},
    'issue': {'category': 5, 'name': 'Issue'},
    'issueDate': {'category': 4, 'name': 'Issue Date'},
    'issuingAuthority': {'category': 5, 'name': 'Issuing Authority'},
    'journalAbbreviation': {'category': 7, 'name': 'Journal Abbr'},
    'label': {'category': 7, 'name': 'Label'},
    'language': {'category': 7, 'name': 'Language'},
    'legalStatus': {'category': 7, 'name': 'Legal Status'},
    'legislativeBody': {'category': 7, 'name': 'Legislative Body'},
    'letterType': {'category': 7, 'name': 'Type'},
    'libraryCatalog': {'category': 6, 'name': 'Library Catalog'},
    'manuscriptType': {'category': 7, 'name': 'Type'},
    'mapType': {'category': 7, 'name': 'Type'},
    'meetingName': {'category': 7, 'name': 'Meeting Name'},
    'nameOfAct': {'category': 7, 'name': 'Name of Act'},
    'network': {'category': 7, 'name': 'Network'},
    'numPages': {'category': 7, 'name': '# of Pages'},
    'numberOfVolumes': {'category': 7, 'name': '# of Volumes'},
    'pages': {'category': 7, 'name': 'Pages'},
    'patentNumber': {'category': 7, 'name': 'Patent Number'},
    'place': {'category': 5, 'name': 'Place'},
    'postType': {'category': 7, 'name': 'Post Type'},
    'presentationType': {'category': 7, 'name': 'Type'},
    'priorityNumbers': {'category': 7, 'name': 'Priority Numbers'},
    'proceedingsTitle': {'category': 5, 'name': 'Proceedings Title'},
    'programTitle': {'category': 7, 'name': 'Program Title'},
    'programmingLanguage': {'category': 7, 'name': 'Language'},
    'publicLawNumber': {'category': 7, 'name': 'Public Law Number'},
    'publicationTitle': {'category': 5, 'name': 'Publication'},
    'publisher': {'category': 5, 'name': 'Publisher'},
    'references': {'category': 7, 'name': 'References'},
    'reportNumber': {'category': 7, 'name': 'Report Number'},
    'reportType': {'category': 1, 'name': 'Report Type'},
    'reporter': {'category': 7, 'name': 'Reporter'},
    'reporterVolume': {'category': 7, 'name': 'Reporter Volume'},
    'rights': {'category': 7, 'name': 'Rights'},
    'runningTime': {'category': 7, 'name': 'Running Time'},
    'scale': {'category': 7, 'name': 'Scale'},
    'section': {'category': 5, 'name': 'Section'},
    'series': {'category': 5, 'name': 'Series'},
    'seriesNumber': {'category': 5, 'name': 'Series Number'},
    'seriesText': {'category': 5, 'name': 'Series Text'},
    'seriesTitle': {'category': 5, 'name': 'Series Title'},
    'session': {'category': 7, 'name': 'Session'},
    'shortTitle': {'category': 2, 'name': 'Short Title'},
    'studio': {'category': 7, 'name': 'Studio'},
    'subject': {'category': 7, 'name': 'Subject'},
    'system': {'category': 7, 'name': 'System'},
    'thesisType': {'category': 7, 'name': 'Type'},
    'title': {'category': 2, 'name': 'Title'},
    'university': {'category': 7, 'name': 'University'},
    'url': {'category': 7, 'name': 'URL'},
    'version': {'category': 7, 'name': 'Version'},
    'videoRecordingFormat': {'category': 7, 'name': 'Format'},
    'volume': {'category': 5, 'name': 'Volume'},
    'websiteTitle': {'category': 7, 'name': 'Website Title'},
    'websiteType': {'category': 7, 'name': 'Website Type'},
    'itemType': {'category' : 1, 'name' : 'Item Type'}
}
#category_order = {
#    'Item Type' : 1,
#    'Title' : 2,
#    'Creator(s)' : 3,
#    'Date' : 4,
#    'Publication information' : 5,
#    'Location information' : 6,
#    'Misc.' : 7
#}
type_map = {'csl' : {'document': 'article', 'manuscript': 'manuscript', 'radioBroadcast': 'broadcast', 'dictionaryEntry': 'chapter', 'hearing': 'bill', 'thesis': 'thesis', 'film': 'motion_picture', 'conferencePaper': 'paper-conference', 'journalArticle': 'article-journal', 'patent': 'patent', 'webpage': 'webpage', 'book': 'book', 'instantMessage': 'personal_communication', 'interview': 'interview', 'presentation': 'speech', 'email': 'personal_communication', 'forumPost': 'webpage', 'map': 'map', 'videoRecording': 'motion_picture', 'blogPost': 'webpage', 'newspaperArticle': 'article-newspaper', 'letter': 'personal_communication', 'artwork': 'graphic', 'report': 'report', 'podcast': 'song', 'audioRecording': 'song', 'case': 'legal_case', 'statute': 'bill', 'computerProgram': 'book', 'bill': 'bill', 'bookSection': 'chapter', 'tvBroadcast': 'broadcast', 'magazineArticle': 'article-magazine', 'encyclopediaArticle': 'chapter'}, 'readable' : {'forumPost': 'Forum Post', 'map': 'Map', 'instantMessage': 'Instant Message', 'videoRecording': 'Video Recording', 'thesis': 'Thesis', 'manuscript': 'Manuscript', 'radioBroadcast': 'Radio Broadcast', 'blogPost': 'Blog Post', 'dictionaryEntry': 'Dictionary Entry', 'hearing': 'Hearing', 'newspaperArticle': 'Newspaper Article', 'letter': 'Letter', 'artwork': 'Artwork', 'report': 'Report', 'podcast': 'Podcast', 'audioRecording': 'Audio Recording', 'film': 'Film', 'conferencePaper': 'Conference Paper', 'case': 'Case', 'statute': 'Statute', 'computerProgram': 'Computer Program', 'journalArticle': 'Journal Article', 'patent': 'Patent', 'bill': 'Bill', 'bookSection': 'Book Section', 'magazineArticle': 'Magazine Article', 'webpage': 'Webpage', 'book': 'Book', 'encyclopediaArticle': 'Encyclopedia Article', 'interview': 'Interview', 'document': 'Document', 'presentation': 'Presentation', 'email': 'Email', 'tvBroadcast': 'TV Broadcast'} }
contrib_map = {'csl' : {'author': 'author', 'contributor' : 'author', 'bookAuthor': 'container-author', 'seriesEditor': 'collection-editor', 'translator': 'translator', 'editor': 'editor', 'interviewer': 'interviewer', 'recipient': 'recipient', 'interviewee' : 'contributor'}, 'readable' : {'translator': 'Translator', 'contributor': 'Contributor', 'seriesEditor': 'Series Editor', 'editor': 'Editor', 'author': 'Author', 'bookAuthor': 'Book Author', 'recipient': 'Recipient', 'interviewer': 'Interviewer', 'interviewee': 'Interviewee'}}
