from urllib2 import urlopen, HTTPError
from lxml import etree
import re, json

NS = {'xhtml': 'http://www.w3.org/1999/xhtml',
      'zot' : "http://zotero.org/ns/api",
      'atom' : "http://www.w3.org/2005/Atom"}

# Zotero API calls
def get_libraries(zotero_uid, zotero_key):
    url = 'https://api.zotero.org/users/%s/groups?key=%s' % (zotero_uid, zotero_key)
    access = {'zapi_version' : 'null',
              'libraries' : [{'title' : 'Your library',
                              'location': 'https://api.zotero.org/users/%s' % zotero_uid }]}
    for x in parse_xml(url)['items']:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        loc = x.xpath('./atom:link[@rel="self"]', namespaces=NS)[0].attrib['href']
        access['libraries'].append({'title' : title, 'location' : loc })
    return access

def get_collections(zotero_key, loc, top):
    if top:
        url = '%s/collections/top?key=%s&order=title&format=atom&content=json' % (loc, zotero_key)
    else:
        url = '%s/collections?key=%s&format=atom&content=json' % (loc, zotero_key)
    collections = { 'zapi_version' : 'null',
                    'collections' : []}
    for x in parse_xml(url)['items']:
        title = x.xpath('./atom:title', namespaces=NS)[0].text
        loc = x.xpath('./atom:link[@rel="self"]', namespaces=NS)[0].attrib['href']
        has_children = bool(int(x.xpath('./zot:numCollections', namespaces=NS)[0].text))
        collections['collections'].append({ 'title' : title, 'location' : loc, 'has_children' : int(has_children) })
    return collections

def get_items(zotero_key, loc, opts):
    opts = ['%s=%s' % (key, str(opts[key])) for key in opts.keys()]
    url = loc + '/items?key=%s&format=atom&content=json&%s' % (zotero_key, '&'.join(opts))
    latest = { 'zapi_version' : 'null', 'items' : []}
    parsed = parse_xml(url)
    latest['total_items'] = parsed['count']
    for x in parsed['items']:
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
                 'item_type' : type_map['readable'][json.loads(item_json)['itemType']],
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
    
    output = {}
    output['type'] = type_map['csl'][zotero_data['itemType']]
    output['id'] = citeproc_identifier # For use with citeproc-js.
    
    # Translate fields for CSL processing
    zotero_fields = zotero_data.keys()
    skip = ['date', 'creators', 'itemType']
    fields_for_translation = [key for key in zotero_data.keys() if key not in skip and zotero_data[key]]
    for field in fields_for_translation:
        try:
            output[csl_map[field]] = zotero_data[field]
        except KeyError:
            pass
    if 'creators' in zotero_fields:
        names = resolve_names(zotero_data, 'csl')
        for contrib_type in names.keys():
            output[contrib_type] = names[contrib_type]
    if 'date' in zotero_fields:
        output['issued'] = { 'raw' : zotero_data['date'] }
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
            try:
                contribs.setdefault(contrib_map['csl'][creator['creatorType']], []).append(name)
            except KeyError:
                pass

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
    try:
        page = urlopen(url)
        xml_parse = etree.parse(page)
        page.close()
        root = xml_parse.getroot()
        return {'items' : root.xpath('./atom:entry', namespaces=NS),
                'count' : root.xpath('./zot:totalResults', namespaces=NS)[0].text}
    except HTTPError, error:
        error_content = error.read()
        raise Exception

# Map to translate JSON from Zotero to something understandable by citeproc-js CSL engine.
# See http://gsl-nagoya-u.net/http/pub/csl-fields/
csl_map = {
    "publicationTitle": "container-title", 
    "letterType": "genre", 
    "DOI": "DOI", 
    "ISBN": "ISBN", 
    "meetingName": "event", 
    "bookTitle": "container-title", 
    "extra": "note", 
    "series": "collection-title", 
    "caseName": "title", 
    "blogTitle": "container-title", 
    "codeVolume": "volume", 
    "edition": "edition", 
    "code": "container-title", 
    "references": "references", 
    "distributor": "publisher", 
    "seriesNumber": "collection-number", 
    "abstractNote": "abstract", 
    "label": "publisher", 
    "dateEnacted": "issued", 
    "archive": "archive", 
    "numberOfVolumes": "number-of-volumes", 
    "subject": "title", 
    "encyclopediaTitle": "container-title", 
    "episodeNumber": "number", 
    "programTitle": "container-title", 
    "court": "authority", 
    "network": "publisher", 
    "title": "title", 
    "proceedingsTitle": "container-title", 
    "section": "section", 
    "reporter": "container-title", 
    "forumTitle": "container-title", 
    "archiveLocation": "archive_location", 
    "documentNumber": "number", 
    "version": "version", 
    "websiteType": "genre", 
    "mapType": "genre", 
    "postType": "genre", 
    "presentationType": "genre", 
    "dictionaryTitle": "container-title", 
    "videoRecordingFormat": "medium", 
    "issue": "issue", 
    "company": "publisher", 
    "nameOfAct": "title", 
    "seriesTitle": "collection-title", 
    "thesisType": "genre", 
    "institution": "publisher", 
    "patentNumber": "number", 
    "accessDate": "accessed", 
    "manuscriptType": "genre", 
    "billNumber": "number", 
    "firstPage": "page", 
    "volume": "volume", 
    "callNumber": "call-number", 
    "reporterVolume": "volume", 
    "studio": "publisher", 
    "publicLawNumber": "number", 
    "reportNumber": "number", 
    "genre": "genre", 
    "interviewMedium": "medium", 
    "codePages": "page", 
    "pages": "page", 
    "numPages": "number-of-pages", 
    "publisher": "publisher", 
    "dateDecided": "issued", 
    "language": "language", 
    "audioRecordingFormat": "medium", 
    "conferenceName": "event", 
    "url": "URL", 
    "issueDate": "issued", 
    "university": "publisher", 
    "rights": "rights", 
    "artworkMedium": "medium", 
    "artworkSize": "genre", 
    "audioFileType": "medium", 
    "place": "publisher-place", 
    "docketNumber": "number", 
    "reportType": "genre", 
    "websiteTitle": "container-title", 
    "history": "references"
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
