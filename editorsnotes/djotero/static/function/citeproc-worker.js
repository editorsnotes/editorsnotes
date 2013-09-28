var EditorsNotes = {}
  , scripts = [
    'citeproc-js/xmljson.js',
    'citeproc-js/citeproc.js',
    'zotero-jquery/csl.js',
    'zotero-jquery/formats.js',
    'zotero-jquery/locales.js',
    'zotero-jquery/z2csl.js',
  ]

scripts.forEach(function (path) { importScripts('/static/function/' + path) });

var engine = EditorsNotes.CSL.createCSLEngine('chicago-fullnote-bibliography');
var xml = EditorsNotes.CSL.currentEngine.sys.xml;
var z2csl = EditorsNotes.CSL.z2CSL;

cslTypes = xml.getNodesByName(z2csl, 'typemap');
cslCreators = xml.getNodesByName(z2csl, 'creatorMap');
cslFields = xml.getNodesByName(z2csl, 'fieldMap');

function getCSLTypeNode(zoteroItemType) {
  var zType
    , cslType

  for (var i = 0; i < cslTypes.length; i++) {
    zType = xml.getAttributeValue(cslTypes[i], 'zType');
    if (zType === zoteroItemType) {
      cslType = xml.getAttributeValue(cslTypes[i], 'cslType');
      break;
    }
  }
  return cslType;
}

function getCSLField(zoteroField) {
  var zField
    , cslField

  for (var i = 0; i < cslFields.length; i++) {
    zField = xml.getAttributeValue(cslFields[i], 'zField');
    if (zField === zoteroField) {
      cslField = xml.getAttributeValue(cslFields[i], 'cslField');
    }
  }
  return cslField;
}

function getCSLCreatorType(zoteroCreatorType) {
  var zCreator
    , cslCreator

  for (var i = 0; i < cslCreators.length; i++) {
    zCreator = xml.getAttributeValue(cslCreators[i], 'zCreator');
    if (zCreator === zoteroCreatorType) {
      cslCreator = xml.getAttributeValue(cslCreators[i], 'cslCreator');
      break;
    }
  }
  return cslCreator;
}

function zoteroToCSL(zoteroData) {
  var cslObject = {}
    , typeNode = getCSLTypeNode(zoteroData.itemType)
    , val
    , cslKey

  for (var key in zoteroData) {
    val = zoteroData[key];
    if (!val.length) continue;
    switch (key) {
      case 'itemType':
      case 'tags':
        // Not used
        break;
      case 'creators':
        val.forEach(function (creator) {
          var cslCreatorObject = {}
            , cslCreatorType = getCSLCreatorType(creator.creatorType)

          if (! (creator.firstName || creator.lastName || creator.name ) ) {
            return;
          }
          
          if (!cslObject.hasOwnProperty(cslCreatorType)) {
            cslObject[cslCreatorType] = [];
          }

          if (creator.firstName || creator.lastname) {
            if (creator.firstName) cslCreatorObject.given = creator.firstName;
            if (creator.lastName) cslCreatorObject.family = creator.lastName;
          } else {
            cslCreatorObject.literal = creator.name;
          }

          cslObject[cslCreatorType].push(cslCreatorObject);
        });
        break;
      case 'date':
        cslObject.issued = { 'raw': val };
        break;
      default:
        // doesn't yet do the baseField thing
        cslKey = getCSLField(key);
        if (cslKey) {
          cslObject[cslKey] = val;
        }
        break;
    }
  }

  return cslObject;
}


self.addEventListener('message', function (e) {
  var data = e.data.zotero_data
    , csl = zoteroToCSL(data)
    , citation = engine(csl)

  if (citation.match(/\[CSL STYLE ERROR: reference with no printed form/)) {
    citation = '';
  }

  self.postMessage({ data: data, csl: csl, citation: citation });
}, false);
