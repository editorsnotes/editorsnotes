
  var zoteroFormToObject = function($form, sorted) {
    // Given a form rendered with buildZoteroForm above, create two different
    // objects: an array that preserves the order of they fields, and an object
    // that doesn't. The former is meant to be passed to the server, the latter
    // to a CSL engine
    var zoteroObject = {},
      sortedZoteroObject = {'fields' : []},
      $fields = $form.find('.zotero-entry'),
      creatorsidx,
      tagsix;
    $.each($fields, function(key, val) {
      var $field = $(val),
        fieldKey = $field.data('zotero-key'),
        fieldValue,
        fieldObject = {};
        switch (fieldKey) {
          case 'itemType':
            fieldValue = $field.find('input[type="hidden"]').val();
            zoteroObject.itemType = fieldValue;
            sortedZoteroObject.fields.push({'itemType': fieldValue});
            break;
          case 'creators':
            if (!zoteroObject.creators) {
              zoteroObject.creators = [];
              creatorsidx = sortedZoteroObject.fields.push({'creators': []});
            }
            fieldValue = $(val).find('input[type="hidden"]').val();
            zoteroObject.creators.push( JSON.parse(fieldValue) );
            sortedZoteroObject.fields[creatorsidx - 1].creators.push( JSON.parse(fieldValue) );
            break;
          case 'tags':
            if (!zoteroObject.tags) {
              zoteroObject.tags = [];
              tagsidx = sortedZoteroObject.fields.push({'tags': []});
            }
            fieldValue = $(val).find('input[type="hidden"]').val();
            zoteroObject.creators.push( JSON.parse(fieldValue) );
            sortedZoteroObject.fields[tagsidx - 1].tags.push( JSON.parse(fieldValue) );
            break;
          default:
            fieldValue = $(val).find('textarea').val();
            zoteroObject[fieldKey] = fieldValue;
            fieldObject[fieldKey] = fieldValue;
            sortedZoteroObject.fields.push(fieldObject);
            break;
        }
    });
    if (sorted == true) {
      return sortedZoteroObject;
    }
    return zoteroObject
  };

  var zoteroWymSettings = {
    skin: 'custom',
    toolsItems: [
      {'name': 'Bold', 'title': 'Strong', 'css': 'wym_tools_strong'}, 
      {'name': 'Italic', 'title': 'Emphasis', 'css': 'wym_tools_emphasis'},
    ],
    containersHtml: '',
    classesHtml: '',
    updateSelector: '#document-save',
    updateEvent: 'click',
    classHtml: '',
    postInit: function() {
      var $documentwym = this;
      $($documentwym._iframe).css('height', '92px');
      var generateCiteLink = $('' +
          '<a style="width: 100px;" id="generate-citation" href="#_">Generate citation</a>')
        generateCiteLink.click(function(event, auto) {
          var zoteroForm = $('div.zotero-information'),
            zoteroString;
          if (!zoteroForm.length && auto == undefined) {
            alert('Fill in zotero information to generate citation');
            return true;
          }
          zoteroString = JSON.stringify( zoteroFormToObject(zoteroForm) );
          $.ajax({
            url: '/api/document/csl/',
            data: {'zotero-json': zoteroString},
            success: function(data) {
              var formattedRef = runCite( JSON.stringify(data) );
              if (formattedRef.match(/reference with no printed form/)) {
                formattedRef = '';
              }
              $documentwym.html(formattedRef);
            }
          });
        });
      $(this._box).find(this._options.toolsSelector + this._options.toolsListSelector)
        .append(generateCiteLink);
      }
    }
