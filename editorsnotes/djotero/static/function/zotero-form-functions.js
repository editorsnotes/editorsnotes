$(document).ready(function() {

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

  $('.document-description-edit .xhtml-textarea').wymeditor({
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
    postInit: function(wym) {

      var generateCiteLink = $('<a>', {
        css: {'width': '100px'},
        id: 'wym-editor-generate-citation',
        href: '#',
        text: 'Generate citation',
        click: function(event) {
          var zoteroForm = $('.zotero-information-edit'),
            zoteroString;

          event.preventDefault();

          if (!zoteroForm.find('input').length) {
            alert('Fill in zotero information to generate citation');
            return true;
          }
          zoteroString = JSON.stringify( zoteroFormToObject(zoteroForm) );
          $.get('/api/document/csl/', {'zotero-json': zoteroString}, function(data) {
            var formattedRef = runCite(JSON.stringify(data));
            if (formattedRef.match(/reference with no printed form/)) {
              formattedRef = '';
            }
            wym.html('<p>' + formattedRef + '</p>');
          });
        }
      });

      $(wym._iframe)
        .css('height', '92px');
      $(wym._box)
        .find(wym._options.toolsListSelector)
        .append(generateCiteLink);
    }
  });

  // Bindings
  $('.zotero-information-edit')
    // Get form on creator type change
    .on('change', 'select[name="item-type-select"]', function() {
      var $itemTypeSelect = $(this),
        $zoteroContainer = $itemTypeSelect.parents('.zotero-information-edit'),
        itemType = $itemTypeSelect.val();
      if (itemType.length) {
        $.ajax({
          url: '/api/document/template/',
          data: {'itemType': itemType},
          success: function(data) {
            $zoteroContainer.data('itemTypeSelect', $itemTypeSelect.parents('.control-group'));

            $zoteroContainer
              .html($(data).closest('.zotero-information-edit').html())
              .find('.zotero-entry-delete').remove();
          }
        });
      }
    })

    // Update creators' hidden inputs as they're changed
    .on('input', '.zotero-creator', function() {
      var $this = $(this),
        $creatorAttrs = $this.find('.creator-attr'),
        creatorObject = {};
      $creatorAttrs.each(function() {
        creatorObject[$(this).data('creator-key')] = this.value;
      });
      $this.find('input[type="hidden"]').val(JSON.stringify(creatorObject));
    })

    // Buttons for adding/removing creators
    .on('click', '.zotero-creator .add-creator', function() {
      var $oldCreator = $(this).parents('.zotero-creator'),
        $newCreator = $oldCreator.clone(true, true).insertAfter($oldCreator);
      $newCreator.find('textarea').val('').trigger('input');
    })
    .on('click', '.zotero-creator .remove-creator', function() {
      var $thisRow = $(this).parents('.zotero-creator');
      if ($thisRow.siblings('.zotero-creator').length) {
        $thisRow.remove();
      }
    });
});
