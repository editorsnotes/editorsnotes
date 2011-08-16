from urllib2 import urlopen
from lxml import etree
import re, json

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
            item_csl = convert_zotero_json(item_json, 'csl')
            latest['items'].append({'title' : title, 'loc' : loc, 'id' : item_id, 'url' : library_url, 'item_json' : item_json, 'item_csl' : item_csl })
    return latest

def convert_zotero_json(obj, output_format):
    # option must be 'csl' or 'readable'
    #
    # Next lines are necessary so that data can be
    # passed either as a string or a dictionary
    try:
        zotero_data = obj
        genre = zotero_data['itemType']
    except:
        zotero_data = json.loads(obj)
        genre = zotero_data['itemType']

    field_translation = field_map[genre][output_format]
    output = {}
    for old, new in field_translation.items():
        if zotero_data[old]:
            output[new] = zotero_data[old]
    if zotero_data['creators']:
        names = get_names(zotero_data, output_format)
        for contrib_type in names.keys():
            output[contrib_type] = names[contrib_type]
    if output_format == 'csl':
        output['type'] = type_map['csl'][genre]
        output['id'] = 'ITEM-1' # For use with citeproc-js.
        try:
            if zotero_data['date']:
                output['issued'] = { 'raw' : zotero_data['date'] }
        except KeyError:
            if zotero_data['dateDecided']:
                output['issued'] = { 'raw' : zotero_data['dateDecided'] }
    elif output_format == 'readable':
        output['Item Type'] = type_map['readable'][genre]
    return json.dumps(output)

def get_names(namelist, format):
    contribs = {}
    for c in namelist['creators']:
        if format == 'csl':
            try:
                name = { "family" : c['lastName'], "given" : c['firstName'] }
            except:
                name = { "literal" : c['name'] }
        elif format == 'readable':
            try:
                name = c['lastName'] + ', ' + c['firstName']
            except:
                name = c['name']
        
        contribs.setdefault(contrib_map[format][c['creatorType']], []).append(name)

        if format == 'readable':
        # Combine lists of names for display. Fix this later to list contribs separately.
            for creator_type in contribs.keys():
                if len(contribs[creator_type]) == 1:
                    contribs[creator_type] = contribs[creator_type][0]
                    break
                elif len(contribs[creator_type]) == 2:
                    contribs[creator_type] = ' and '.join(contribs[creator_type])
                    break
                else:
                    contribs[creator_type] = '; '.join(contribs[creator_type])
                    break
    return contribs

# Maps to translate json from Zotero's API to CSL or human-readable form,
# see http://gsl-nagoya-u.net/http/pub/csl-fields/

field_map = {
    "forumPost": {
        "csl": {
            "title": "title", 
            "url": "URL", 
            "extra": "note", 
            "accessDate": "accessed", 
            "postType": "genre", 
            "abstractNote": "abstract", 
            "forumTitle": "container-title"
        }, 
        "readable": {
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "forumTitle": "Forum/Listserv Title", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "postType": "Post Type"
        }
    }, 
    "map": {
        "csl": {
            "seriesTitle": "collection-title", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "accessDate": "accessed", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "publisher": "publisher", 
            "edition": "edition", 
            "url": "URL", 
            "title": "title", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place", 
            "mapType": "genre"
        }, 
        "readable": {
            "seriesTitle": "Series Title", 
            "publisher": "Publisher", 
            "scale": "Scale", 
            "ISBN": "ISBN", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "extra": "Extra", 
            "libraryCatalog": "Library Catalog", 
            "edition": "Edition", 
            "accessDate": "Accessed", 
            "place": "Place", 
            "mapType": "Type", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "archiveLocation": "Loc. in Archive", 
            "archive": "Archive", 
            "callNumber": "Call Number"
        }
    }, 
    "videoRecording": {
        "csl": {
            "seriesTitle": "collection-title", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "accessDate": "accessed", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "studio": "publisher", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "numberOfVolumes": "number-of-volumes", 
            "title": "title", 
            "url": "URL", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place", 
            "videoRecordingFormat": "medium"
        }, 
        "readable": {
            "seriesTitle": "Series Title", 
            "ISBN": "ISBN", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "archiveLocation": "Loc. in Archive", 
            "title": "Title", 
            "libraryCatalog": "Library Catalog", 
            "archive": "Archive", 
            "volume": "Volume", 
            "runningTime": "Running Time", 
            "accessDate": "Accessed", 
            "place": "Place", 
            "date": "Date", 
            "studio": "Studio", 
            "numberOfVolumes": "# of Volumes", 
            "videoRecordingFormat": "Format", 
            "extra": "Extra", 
            "abstractNote": "Abstract", 
            "callNumber": "Call Number"
        }
    }, 
    "letter": {
        "csl": {
            "callNumber": "call-number", 
            "letterType": "genre", 
            "accessDate": "accessed", 
            "extra": "note", 
            "url": "URL", 
            "abstractNote": "abstract", 
            "title": "title", 
            "archiveLocation": "archive_location", 
            "archive": "archive"
        }, 
        "readable": {
            "letterType": "Type", 
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "libraryCatalog": "Library Catalog", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "archive": "Archive", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "archiveLocation": "Loc. in Archive"
        }
    }, 
    "manuscript": {
        "csl": {
            "extra": "note", 
            "accessDate": "accessed", 
            "manuscriptType": "genre", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "numPages": "number-of-pages", 
            "title": "title", 
            "url": "URL", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place"
        }, 
        "readable": {
            "numPages": "# of Pages", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "manuscriptType": "Type", 
            "extra": "Extra", 
            "libraryCatalog": "Library Catalog", 
            "accessDate": "Accessed", 
            "place": "Place", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "archiveLocation": "Loc. in Archive", 
            "archive": "Archive", 
            "callNumber": "Call Number"
        }
    }, 
    "radioBroadcast": {
        "csl": {
            "extra": "note", 
            "accessDate": "accessed", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "episodeNumber": "number", 
            "programTitle": "container-title", 
            "network": "publisher", 
            "audioRecordingFormat": "medium", 
            "title": "title", 
            "url": "URL", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place"
        }, 
        "readable": {
            "extra": "Extra", 
            "episodeNumber": "Episode Number", 
            "programTitle": "Program Title", 
            "language": "Language", 
            "audioRecordingFormat": "Format", 
            "rights": "Rights", 
            "accessDate": "Accessed", 
            "runningTime": "Running Time", 
            "title": "Title", 
            "libraryCatalog": "Library Catalog", 
            "shortTitle": "Short Title", 
            "url": "URL", 
            "place": "Place", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "archiveLocation": "Loc. in Archive", 
            "archive": "Archive", 
            "callNumber": "Call Number", 
            "network": "Network"
        }
    }, 
    "magazineArticle": {
        "csl": {
            "extra": "note", 
            "accessDate": "accessed", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "pages": "page", 
            "title": "title", 
            "url": "URL", 
            "archive": "archive", 
            "archiveLocation": "archive_location", 
            "publicationTitle": "container-title", 
            "issue": "issue"
        }, 
        "readable": {
            "ISSN": "ISSN", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "extra": "Extra", 
            "url": "URL", 
            "issue": "Issue", 
            "rights": "Rights", 
            "libraryCatalog": "Library Catalog", 
            "archive": "Archive", 
            "volume": "Volume", 
            "accessDate": "Accessed", 
            "publicationTitle": "Publication", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "archiveLocation": "Loc. in Archive", 
            "pages": "Pages", 
            "callNumber": "Call Number"
        }
    }, 
    "blogPost": {
        "csl": {
            "extra": "note", 
            "url": "URL", 
            "title": "title", 
            "blogTitle": "container-title", 
            "accessDate": "accessed", 
            "websiteType": "genre", 
            "abstractNote": "abstract"
        }, 
        "readable": {
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "blogTitle": "Blog Title", 
            "websiteType": "Website Type", 
            "title": "Title"
        }
    }, 
    "artwork": {
        "csl": {
            "artworkSize": "genre", 
            "callNumber": "call-number", 
            "accessDate": "accessed", 
            "extra": "note", 
            "url": "URL", 
            "archiveLocation": "archive_location", 
            "title": "title", 
            "artworkMedium": "medium", 
            "abstractNote": "abstract", 
            "archive": "archive"
        }, 
        "readable": {
            "artworkSize": "Artwork Size", 
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "libraryCatalog": "Library Catalog", 
            "artworkMedium": "Medium", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "archive": "Archive", 
            "callNumber": "Call Number", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "archiveLocation": "Loc. in Archive"
        }
    }, 
    "hearing": {
        "csl": {
            "extra": "note", 
            "accessDate": "accessed", 
            "abstractNote": "abstract", 
            "pages": "page", 
            "numberOfVolumes": "number-of-volumes", 
            "publisher": "publisher", 
            "title": "title", 
            "url": "URL", 
            "documentNumber": "number", 
            "place": "publisher-place", 
            "history": "references"
        }, 
        "readable": {
            "extra": "Extra", 
            "publisher": "Publisher", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "accessDate": "Accessed", 
            "documentNumber": "Document Number", 
            "session": "Session", 
            "legislativeBody": "Legislative Body", 
            "committee": "Committee", 
            "date": "Date", 
            "place": "Place", 
            "abstractNote": "Abstract", 
            "pages": "Pages", 
            "numberOfVolumes": "# of Volumes", 
            "history": "History"
        }
    }, 
    "newspaperArticle": {
        "csl": {
            "extra": "note", 
            "accessDate": "accessed", 
            "edition": "edition", 
            "abstractNote": "abstract", 
            "pages": "page", 
            "callNumber": "call-number", 
            "url": "URL", 
            "section": "section", 
            "title": "title", 
            "archive": "archive", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place", 
            "publicationTitle": "container-title"
        }, 
        "readable": {
            "ISSN": "ISSN", 
            "accessDate": "Accessed", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "extra": "Extra", 
            "url": "URL", 
            "section": "Section", 
            "rights": "Rights", 
            "libraryCatalog": "Library Catalog", 
            "archive": "Archive", 
            "edition": "Edition", 
            "publicationTitle": "Publication", 
            "place": "Place", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "archiveLocation": "Loc. in Archive", 
            "pages": "Pages", 
            "callNumber": "Call Number"
        }
    }, 
    "thesis": {
        "csl": {
            "thesisType": "genre", 
            "extra": "note", 
            "accessDate": "accessed", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "numPages": "number-of-pages", 
            "title": "title", 
            "url": "URL", 
            "university": "publisher", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place"
        }, 
        "readable": {
            "numPages": "# of Pages", 
            "thesisType": "Type", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "university": "University", 
            "extra": "Extra", 
            "libraryCatalog": "Library Catalog", 
            "accessDate": "Accessed", 
            "place": "Place", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "archiveLocation": "Loc. in Archive", 
            "archive": "Archive", 
            "callNumber": "Call Number"
        }
    }, 
    "dictionaryEntry": {
        "csl": {
            "publisher": "publisher", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "url": "URL", 
            "series": "collection-title", 
            "title": "title", 
            "numberOfVolumes": "number-of-volumes", 
            "archive": "archive", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "accessDate": "accessed", 
            "place": "publisher-place", 
            "seriesNumber": "collection-number", 
            "archiveLocation": "archive_location", 
            "dictionaryTitle": "container-title", 
            "edition": "edition", 
            "pages": "page", 
            "abstractNote": "abstract"
        }, 
        "readable": {
            "ISBN": "ISBN", 
            "extra": "Extra", 
            "series": "Series", 
            "edition": "Edition", 
            "seriesNumber": "Series Number", 
            "numberOfVolumes": "# of Volumes", 
            "archive": "Archive", 
            "title": "Title", 
            "accessDate": "Accessed", 
            "dictionaryTitle": "Dictionary Title", 
            "archiveLocation": "Loc. in Archive", 
            "libraryCatalog": "Library Catalog", 
            "volume": "Volume", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "pages": "Pages", 
            "abstractNote": "Abstract", 
            "publisher": "Publisher", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "place": "Place"
        }
    }, 
    "report": {
        "csl": {
            "seriesTitle": "collection-title", 
            "extra": "note", 
            "accessDate": "accessed", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "institution": "publisher", 
            "reportNumber": "number", 
            "url": "URL", 
            "title": "title", 
            "pages": "page", 
            "archiveLocation": "archive_location", 
            "archive": "archive", 
            "place": "publisher-place", 
            "reportType": "genre"
        }, 
        "readable": {
            "seriesTitle": "Series Title", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "archiveLocation": "Loc. in Archive", 
            "title": "Title", 
            "libraryCatalog": "Library Catalog", 
            "pages": "Pages", 
            "accessDate": "Accessed", 
            "archive": "Archive", 
            "place": "Place", 
            "reportNumber": "Report Number", 
            "date": "Date", 
            "reportType": "Report Type", 
            "abstractNote": "Abstract", 
            "extra": "Extra", 
            "institution": "Institution", 
            "callNumber": "Call Number"
        }
    }, 
    "podcast": {
        "csl": {
            "seriesTitle": "collection-title", 
            "episodeNumber": "number", 
            "accessDate": "accessed", 
            "extra": "note", 
            "url": "URL", 
            "title": "title", 
            "abstractNote": "abstract", 
            "audioFileType": "medium"
        }, 
        "readable": {
            "seriesTitle": "Series Title", 
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "runningTime": "Running Time", 
            "abstractNote": "Abstract", 
            "episodeNumber": "Episode Number", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "audioFileType": "File Type"
        }
    }, 
    "audioRecording": {
        "csl": {
            "seriesTitle": "collection-title", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "accessDate": "accessed", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "numberOfVolumes": "number-of-volumes", 
            "audioRecordingFormat": "medium", 
            "title": "title", 
            "url": "URL", 
            "label": "publisher", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place"
        }, 
        "readable": {
            "seriesTitle": "Series Title", 
            "ISBN": "ISBN", 
            "language": "Language", 
            "audioRecordingFormat": "Format", 
            "rights": "Rights", 
            "url": "URL", 
            "extra": "Extra", 
            "libraryCatalog": "Library Catalog", 
            "shortTitle": "Short Title", 
            "label": "Label", 
            "volume": "Volume", 
            "runningTime": "Running Time", 
            "archive": "Archive", 
            "accessDate": "Accessed", 
            "place": "Place", 
            "date": "Date", 
            "title": "Title", 
            "numberOfVolumes": "# of Volumes", 
            "archiveLocation": "Loc. in Archive", 
            "abstractNote": "Abstract", 
            "callNumber": "Call Number"
        }
    }, 
    "film": {
        "csl": {
            "extra": "note", 
            "accessDate": "accessed", 
            "callNumber": "call-number", 
            "genre": "genre", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "title": "title", 
            "url": "URL", 
            "distributor": "publisher", 
            "archiveLocation": "archive_location", 
            "videoRecordingFormat": "medium"
        }, 
        "readable": {
            "date": "Date", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "accessDate": "Accessed", 
            "runningTime": "Running Time", 
            "extra": "Extra", 
            "libraryCatalog": "Library Catalog", 
            "genre": "Genre", 
            "url": "URL", 
            "distributor": "Distributor", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "videoRecordingFormat": "Format", 
            "archiveLocation": "Loc. in Archive", 
            "archive": "Archive", 
            "callNumber": "Call Number"
        }
    }, 
    "conferencePaper": {
        "csl": {
            "publisher": "publisher", 
            "DOI": "DOI", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "url": "URL", 
            "series": "collection-title", 
            "title": "title", 
            "archive": "archive", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "accessDate": "accessed", 
            "place": "publisher-place", 
            "proceedingsTitle": "container-title", 
            "archiveLocation": "archive_location", 
            "abstractNote": "abstract", 
            "conferenceName": "event", 
            "pages": "page"
        }, 
        "readable": {
            "DOI": "DOI", 
            "ISBN": "ISBN", 
            "extra": "Extra", 
            "series": "Series", 
            "conferenceName": "Conference Name", 
            "abstractNote": "Abstract", 
            "archive": "Archive", 
            "title": "Title", 
            "proceedingsTitle": "Proceedings Title", 
            "accessDate": "Accessed", 
            "archiveLocation": "Loc. in Archive", 
            "libraryCatalog": "Library Catalog", 
            "volume": "Volume", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "pages": "Pages", 
            "publisher": "Publisher", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "place": "Place"
        }
    }, 
    "case": {
        "csl": {
            "caseName": "title", 
            "reporter": "container-title", 
            "accessDate": "accessed", 
            "firstPage": "page", 
            "reporterVolume": "volume", 
            "abstractNote": "abstract", 
            "court": "authority", 
            "url": "URL", 
            "extra": "note", 
            "docketNumber": "number", 
            "dateDecided": "issued", 
            "history": "references"
        }, 
        "readable": {
            "caseName": "Case Name", 
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "firstPage": "First Page", 
            "reporterVolume": "Reporter Volume", 
            "abstractNote": "Abstract", 
            "court": "Court", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "reporter": "Reporter", 
            "docketNumber": "Docket Number", 
            "dateDecided": "Date Decided", 
            "history": "History"
        }
    }, 
    "statute": {
        "csl": {
            "code": "container-title", 
            "extra": "note", 
            "accessDate": "accessed", 
            "publicLawNumber": "number", 
            "abstractNote": "abstract", 
            "pages": "page", 
            "url": "URL", 
            "section": "section", 
            "dateEnacted": "issued", 
            "history": "references", 
            "nameOfAct": "title"
        }, 
        "readable": {
            "code": "Code", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "codeNumber": "Code Number", 
            "extra": "Extra", 
            "dateEnacted": "Date Enacted", 
            "pages": "Pages", 
            "accessDate": "Accessed", 
            "session": "Session", 
            "publicLawNumber": "Public Law Number", 
            "abstractNote": "Abstract", 
            "history": "History", 
            "section": "Section", 
            "nameOfAct": "Name of Act"
        }
    }, 
    "computerProgram": {
        "csl": {
            "seriesTitle": "collection-title", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "accessDate": "accessed", 
            "company": "publisher", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "title": "title", 
            "url": "URL", 
            "archiveLocation": "archive_location", 
            "version": "version", 
            "place": "publisher-place"
        }, 
        "readable": {
            "seriesTitle": "Series Title", 
            "ISBN": "ISBN", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "programmingLanguage": "Language", 
            "extra": "Extra", 
            "libraryCatalog": "Library Catalog", 
            "system": "System", 
            "archive": "Archive", 
            "accessDate": "Accessed", 
            "version": "Version", 
            "place": "Place", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "archiveLocation": "Loc. in Archive", 
            "company": "Company", 
            "callNumber": "Call Number"
        }
    }, 
    "journalArticle": {
        "csl": {
            "seriesTitle": "collection-title", 
            "DOI": "DOI", 
            "extra": "note", 
            "accessDate": "accessed", 
            "series": "collection-title", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "pages": "page", 
            "title": "title", 
            "url": "URL", 
            "archive": "archive", 
            "archiveLocation": "archive_location", 
            "publicationTitle": "container-title", 
            "issue": "issue"
        }, 
        "readable": {
            "DOI": "DOI", 
            "extra": "Extra", 
            "seriesText": "Series Text", 
            "series": "Series", 
            "abstractNote": "Abstract", 
            "archive": "Archive", 
            "title": "Title", 
            "ISSN": "ISSN", 
            "archiveLocation": "Loc. in Archive", 
            "journalAbbreviation": "Journal Abbr", 
            "issue": "Issue", 
            "seriesTitle": "Series Title", 
            "accessDate": "Accessed", 
            "libraryCatalog": "Library Catalog", 
            "volume": "Volume", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "pages": "Pages", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "publicationTitle": "Publication"
        }
    }, 
    "patent": {
        "csl": {
            "patentNumber": "number", 
            "accessDate": "accessed", 
            "references": "references", 
            "extra": "note", 
            "url": "URL", 
            "place": "publisher-place", 
            "abstractNote": "abstract", 
            "title": "title", 
            "issueDate": "issued", 
            "pages": "page"
        }, 
        "readable": {
            "patentNumber": "Patent Number", 
            "title": "Title", 
            "filingDate": "Filing Date", 
            "language": "Language", 
            "rights": "Rights", 
            "accessDate": "Accessed", 
            "country": "Country", 
            "extra": "Extra", 
            "shortTitle": "Short Title", 
            "applicationNumber": "Application Number", 
            "issuingAuthority": "Issuing Authority", 
            "assignee": "Assignee", 
            "priorityNumbers": "Priority Numbers", 
            "references": "References", 
            "url": "URL", 
            "place": "Place", 
            "legalStatus": "Legal Status", 
            "issueDate": "Issue Date", 
            "pages": "Pages", 
            "abstractNote": "Abstract"
        }
    }, 
    "bill": {
        "csl": {
            "code": "container-title", 
            "extra": "note", 
            "accessDate": "accessed", 
            "codeVolume": "volume", 
            "abstractNote": "abstract", 
            "codePages": "page", 
            "billNumber": "number", 
            "title": "title", 
            "url": "URL", 
            "section": "section", 
            "history": "references"
        }, 
        "readable": {
            "billNumber": "Bill Number", 
            "code": "Code", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "section": "Section", 
            "extra": "Extra", 
            "codeVolume": "Code Volume", 
            "accessDate": "Accessed", 
            "session": "Session", 
            "legislativeBody": "Legislative Body", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "codePages": "Code Pages", 
            "history": "History"
        }
    }, 
    "bookSection": {
        "csl": {
            "publisher": "publisher", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "url": "URL", 
            "series": "collection-title", 
            "bookTitle": "container-title", 
            "title": "title", 
            "numberOfVolumes": "number-of-volumes", 
            "archive": "archive", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "accessDate": "accessed", 
            "place": "publisher-place", 
            "archiveLocation": "archive_location", 
            "seriesNumber": "collection-number", 
            "edition": "edition", 
            "pages": "page", 
            "abstractNote": "abstract"
        }, 
        "readable": {
            "ISBN": "ISBN", 
            "extra": "Extra", 
            "series": "Series", 
            "edition": "Edition", 
            "seriesNumber": "Series Number", 
            "numberOfVolumes": "# of Volumes", 
            "archive": "Archive", 
            "title": "Title", 
            "accessDate": "Accessed", 
            "archiveLocation": "Loc. in Archive", 
            "bookTitle": "Book Title", 
            "libraryCatalog": "Library Catalog", 
            "volume": "Volume", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "pages": "Pages", 
            "abstractNote": "Abstract", 
            "publisher": "Publisher", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "place": "Place"
        }
    }, 
    "tvBroadcast": {
        "csl": {
            "extra": "note", 
            "accessDate": "accessed", 
            "callNumber": "call-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "episodeNumber": "number", 
            "programTitle": "container-title", 
            "network": "publisher", 
            "title": "title", 
            "url": "URL", 
            "archiveLocation": "archive_location", 
            "place": "publisher-place", 
            "videoRecordingFormat": "medium"
        }, 
        "readable": {
            "episodeNumber": "Episode Number", 
            "programTitle": "Program Title", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "accessDate": "Accessed", 
            "runningTime": "Running Time", 
            "extra": "Extra", 
            "libraryCatalog": "Library Catalog", 
            "url": "URL", 
            "place": "Place", 
            "date": "Date", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "videoRecordingFormat": "Format", 
            "archiveLocation": "Loc. in Archive", 
            "archive": "Archive", 
            "callNumber": "Call Number", 
            "network": "Network"
        }
    }, 
    "webpage": {
        "csl": {
            "title": "title", 
            "url": "URL", 
            "extra": "note", 
            "accessDate": "accessed", 
            "websiteType": "genre", 
            "abstractNote": "abstract", 
            "websiteTitle": "container-title"
        }, 
        "readable": {
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "websiteType": "Website Type", 
            "websiteTitle": "Website Title"
        }
    }, 
    "book": {
        "csl": {
            "numPages": "number-of-pages", 
            "publisher": "publisher", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "url": "URL", 
            "series": "collection-title", 
            "title": "title", 
            "edition": "edition", 
            "callNumber": "call-number", 
            "accessDate": "accessed", 
            "place": "publisher-place", 
            "archiveLocation": "archive_location", 
            "seriesNumber": "collection-number", 
            "abstractNote": "abstract", 
            "archive": "archive", 
            "numberOfVolumes": "number-of-volumes", 
            "volume": "volume"
        }, 
        "readable": {
            "ISBN": "ISBN", 
            "extra": "Extra", 
            "series": "Series", 
            "edition": "Edition", 
            "seriesNumber": "Series Number", 
            "numberOfVolumes": "# of Volumes", 
            "archive": "Archive", 
            "title": "Title", 
            "accessDate": "Accessed", 
            "archiveLocation": "Loc. in Archive", 
            "libraryCatalog": "Library Catalog", 
            "volume": "Volume", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "numPages": "# of Pages", 
            "publisher": "Publisher", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "place": "Place"
        }
    }, 
    "instantMessage": {
        "csl": {
            "url": "URL", 
            "accessDate": "accessed", 
            "abstractNote": "abstract", 
            "extra": "note", 
            "title": "title"
        }, 
        "readable": {
            "accessDate": "Accessed", 
            "date": "Date", 
            "shortTitle": "Short Title", 
            "language": "Language", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "abstractNote": "Abstract", 
            "extra": "Extra"
        }
    }, 
    "interview": {
        "csl": {
            "callNumber": "call-number", 
            "interviewMedium": "medium", 
            "accessDate": "accessed", 
            "extra": "note", 
            "url": "URL", 
            "abstractNote": "abstract", 
            "title": "title", 
            "archiveLocation": "archive_location", 
            "archive": "archive"
        }, 
        "readable": {
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "libraryCatalog": "Library Catalog", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "interviewMedium": "Medium", 
            "archive": "Archive", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "archiveLocation": "Loc. in Archive"
        }
    }, 
    "presentation": {
        "csl": {
            "accessDate": "accessed", 
            "presentationType": "genre", 
            "place": "publisher-place", 
            "meetingName": "event", 
            "extra": "note", 
            "url": "URL", 
            "abstractNote": "abstract", 
            "title": "title"
        }, 
        "readable": {
            "meetingName": "Meeting Name", 
            "extra": "Extra", 
            "accessDate": "Accessed", 
            "date": "Date", 
            "abstractNote": "Abstract", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "title": "Title", 
            "place": "Place", 
            "presentationType": "Type"
        }
    }, 
    "email": {
        "csl": {
            "url": "URL", 
            "accessDate": "accessed", 
            "abstractNote": "abstract", 
            "subject": "title", 
            "extra": "note"
        }, 
        "readable": {
            "accessDate": "Accessed", 
            "date": "Date", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "abstractNote": "Abstract", 
            "extra": "Extra", 
            "subject": "Subject"
        }
    }, 
    "encyclopediaArticle": {
        "csl": {
            "publisher": "publisher", 
            "ISBN": "ISBN", 
            "extra": "note", 
            "url": "URL", 
            "series": "collection-title", 
            "title": "title", 
            "numberOfVolumes": "number-of-volumes", 
            "archive": "archive", 
            "volume": "volume", 
            "callNumber": "call-number", 
            "accessDate": "accessed", 
            "place": "publisher-place", 
            "archiveLocation": "archive_location", 
            "seriesNumber": "collection-number", 
            "edition": "edition", 
            "encyclopediaTitle": "container-title", 
            "pages": "page", 
            "abstractNote": "abstract"
        }, 
        "readable": {
            "ISBN": "ISBN", 
            "extra": "Extra", 
            "series": "Series", 
            "edition": "Edition", 
            "seriesNumber": "Series Number", 
            "numberOfVolumes": "# of Volumes", 
            "archive": "Archive", 
            "title": "Title", 
            "accessDate": "Accessed", 
            "archiveLocation": "Loc. in Archive", 
            "libraryCatalog": "Library Catalog", 
            "volume": "Volume", 
            "callNumber": "Call Number", 
            "date": "Date", 
            "pages": "Pages", 
            "abstractNote": "Abstract", 
            "publisher": "Publisher", 
            "language": "Language", 
            "shortTitle": "Short Title", 
            "rights": "Rights", 
            "url": "URL", 
            "place": "Place", 
            "encyclopediaTitle": "Encyclopedia Title"
        }
    },
    "document" : {
        "csl" : {
            "extra" : "extra",
            "publisher" : "publisher",
            "language" : "language",
            "title" : "title",
            "url" : "URL",
            "rights" : "rights",
            "accessDate" : "accessed",
            "abstractNote" : "abstract",
            "archiveLocation" : "archive_location",
            "archive" : "archive"
        },
        "readable" : {
            "abstractNote": "Abstract Note",
            "accessDate": "Access Date",
            "archive": "Archive",
            "archiveLocation": "Loc. in Archive",
            "callNumber": "Call Number",
            "date": "Date",
            "extra": "Extra",
            "language": "Language",
            "libraryCatalog": "Library Catalog",
            "publisher": "Publisher",
            "rights": "Rights",
            "shortTitle": "Short Title",
            "title": "Title",
            "url": "URL",
        }
    }
}
type_map = {'csl' : {'document': 'article', 'manuscript': 'manuscript', 'radioBroadcast': 'broadcast', 'dictionaryEntry': 'chapter', 'hearing': 'bill', 'thesis': 'thesis', 'film': 'motion_picture', 'conferencePaper': 'paper-conference', 'journalArticle': 'article-journal', 'patent': 'patent', 'webpage': 'webpage', 'book': 'book', 'instantMessage': 'personal_communication', 'interview': 'interview', 'presentation': 'speech', 'email': 'personal_communication', 'forumPost': 'webpage', 'map': 'map', 'videoRecording': 'motion_picture', 'blogPost': 'webpage', 'newspaperArticle': 'article-newspaper', 'letter': 'personal_communication', 'artwork': 'graphic', 'report': 'report', 'podcast': 'song', 'audioRecording': 'song', 'case': 'legal_case', 'statute': 'bill', 'computerProgram': 'book', 'bill': 'bill', 'bookSection': 'chapter', 'tvBroadcast': 'broadcast', 'magazineArticle': 'article-magazine', 'encyclopediaArticle': 'chapter'}, 'readable' : {'forumPost': 'Forum Post', 'map': 'Map', 'instantMessage': 'Instant Message', 'videoRecording': 'Video Recording', 'thesis': 'Thesis', 'manuscript': 'Manuscript', 'radioBroadcast': 'Radio Broadcast', 'blogPost': 'Blog Post', 'dictionaryEntry': 'Dictionary Entry', 'hearing': 'Hearing', 'newspaperArticle': 'Newspaper Article', 'letter': 'Letter', 'artwork': 'Artwork', 'report': 'Report', 'podcast': 'Podcast', 'audioRecording': 'Audio Recording', 'film': 'Film', 'conferencePaper': 'Conference Paper', 'case': 'Case', 'statute': 'Statute', 'computerProgram': 'Computer Program', 'journalArticle': 'Journal Article', 'patent': 'Patent', 'bill': 'Bill', 'bookSection': 'Book Section', 'magazineArticle': 'Magazine Article', 'webpage': 'Webpage', 'book': 'Book', 'encyclopediaArticle': 'Encyclopedia Article', 'interview': 'Interview', 'document': 'Document', 'presentation': 'Presentation', 'email': 'Email', 'tvBroadcast': 'TV Broadcast'} }
contrib_map = {'csl' : {'author': 'author', 'contributor' : 'author', 'bookAuthor': 'container-author', 'seriesEditor': 'collection-editor', 'translator': 'translator', 'editor': 'editor', 'interviewer': 'interviewer', 'recipient': 'recipient', 'interviewee' : 'contributor'}, 'readable' : {'translator': 'Translator', 'contributor': 'Contributor', 'seriesEditor': 'Series Editor', 'editor': 'Editor', 'author': 'Author', 'bookAuthor': 'Book Author', 'recipient': 'Recipient', 'interviewer': 'Interviewer', 'interviewee': 'Interviewee'}}
