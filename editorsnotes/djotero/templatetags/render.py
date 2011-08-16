from django import template
from djotero.utils import as_readable
from collections import defaultdict
import json

register = template.Library()

@register.filter
def readable(obj):
    content = json.loads(as_readable(obj))
    content_sorted = defaultdict(list)
    for item in content.items():
        category = category_dict[item[0]]
        content_sorted[category].append(item)
    html = []
    for category, pairs in sorted(content_sorted.items(), key=lambda n: category_order[n[0]]):
        html.append('<span style="padding-bottom:1em;">')
        for key, value in pairs:
            html.append('<span class="span-4" style="color: gray; font-size: 13px; vertical-align: center;">%s:</span> %s<br>' % (key, value))
        html.append('</span>')
    return '\n'.join(html)

category_order = {
    'Item Type' : 1,
    'Title' : 2,
    'Creator(s)' : 3,
    'Date' : 4,
    'Publication information' : 5,
    'Location information' : 6,
    'Misc.' : 7
}

category_dict = {
    '# of Pages': 'Misc.',
    '# of Volumes': 'Misc.',
    'Abstract': 'Misc.',
    'Accessed': 'Date',
    'Application Number': 'Misc.',
    'Archive': 'Location information',
    'Artwork Size': 'Misc.',
    'Assignee': 'Misc.',
    'Author': 'Creator(s)',
    'Bill Number': 'Misc.',
    'Blog Title': 'Publication information',
    'Book Author': 'Creator(s)',
    'Book Title': 'Publication information',
    'Call Number': 'Location information',
    'Case Name': 'Misc.',
    'Code': 'Misc.',
    'Code Number': 'Misc.',
    'Code Pages': 'Misc.',
    'Code Volume': 'Misc.',
    'Committee': 'Misc.',
    'Company': 'Misc.',
    'Conference Name': 'Misc.',
    'Contributor': 'Creator(s)',
    'Country': 'Misc.',
    'Court': 'Misc.',
    'DOI': 'Misc.',
    'Date': 'Date',
    'Date Decided': 'Date',
    'Date Enacted': 'Date',
    'Dictionary Title': 'Publication information',
    'Distributor': 'Misc.',
    'Docket Number': 'Misc.',
    'Document Number': 'Misc.',
    'Edition': 'Publication information',
    'Editor': 'Creator(s)',
    'Encyclopedia Title': 'Publication information',
    'Episode Number': 'Misc.',
    'Extra': 'Misc.',
    'File Type': 'Misc.',
    'Filing Date': 'Misc.',
    'First Page': 'Misc.',
    'Format': 'Misc.',
    'Forum/Listserv Title': 'Publication information',
    'Genre': 'Misc.',
    'History': 'Misc.',
    'ISBN': 'Misc.',
    'ISSN': 'Misc.',
    'Institution': 'Misc.',
    'Interviewee': 'Creator(s)',
    'Interviewer': 'Creator(s)',
    'Issue': 'Publication information',
    'Issue Date': 'Date',
    'Issuing Authority': 'Publication information',
    'Item Type': 'Item Type',
    'Journal Abbr': 'Misc.',
    'Label': 'Misc.',
    'Language': 'Misc.',
    'Legal Status': 'Misc.',
    'Legislative Body': 'Misc.',
    'Library Catalog': 'Location information',
    'Loc. in Archive': 'Location information',
    'Medium': 'Misc.',
    'Meeting Name': 'Misc.',
    'Name of Act': 'Misc.',
    'Network': 'Misc.',
    'Pages': 'Misc.',
    'Patent Number': 'Misc.',
    'Place': 'Publication information',
    'Post Type': 'Misc.',
    'Priority Numbers': 'Misc.',
    'Proceedings Title': 'Publication information',
    'Program Title': 'Misc.',
    'Public Law Number': 'Misc.',
    'Publication': 'Publication information',
    'Publisher': 'Publication information',
    'Recipient': 'Creator(s)',
    'References': 'Misc.',
    'Report Number': 'Misc.',
    'Report Type': 'Item Type',
    'Reporter': 'Misc.',
    'Reporter Volume': 'Misc.',
    'Rights': 'Misc.',
    'Running Time': 'Misc.',
    'Scale': 'Misc.',
    'Section': 'Publication information',
    'Series': 'Publication information',
    'Series Editor': 'Creator(s)',
    'Series Number': 'Publication information',
    'Series Text': 'Publication information',
    'Series Title': 'Publication information',
    'Session': 'Misc.',
    'Short Title': 'Title',
    'Studio': 'Misc.',
    'Subject': 'Misc.',
    'System': 'Misc.',
    'Title': 'Title',
    'Translator': 'Creator(s)',
    'Type': 'Misc.',
    'URL': 'Misc.',
    'University': 'Misc.',
    'Version': 'Misc.',
    'Volume': 'Publication information',
    'Website Title': 'Misc.',
    'Website Type': 'Misc.'
}
