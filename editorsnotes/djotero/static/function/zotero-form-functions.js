$(document).ready(function() {
  
  var $z2csl = $(z2csl),
    zoteroObjectToCsl,
    zoteroFormToObject,
    initArchiveAutocomplete,
    zoteroForm = $('#zotero-information-edit');

  zoteroObjectToCsl = function(zoteroObject) {
    var cslObject = {},
      $typeMap,
      $cslFieldMap,
      $cslCreatorMap;
      
    $typeMap = $z2csl.find('typeMap[zType="' + zoteroObject.itemType + '"]');
    $cslFieldMap = $z2csl.find('cslFieldMap');
    $cslCreatorMap = $z2csl.find('cslCreatorMap');

    cslObject['type'] = $typeMap.attr('cslType');

    $.each(zoteroObject, function(key, val) {
      var $thisField,
        fieldKey,
        cslKey;
      
      if (!val.length) {
        // you have nothing to show us
        return true;
      }

      switch (key) {

      case 'itemType':
      case 'tags':
        // we don't need you
        break;

      case 'creators':
        $.each(val, function() {
          var creatorObject = {},
            creatorType = this.creatorType,
            cslCreatorKey;

          cslCreatorKey = $typeMap
                       .find('field[value="' + creatorType + '"]')
                       .attr('baseField') || creatorType;

          if (!cslObject[cslCreatorKey]) {
            cslObject[cslCreatorKey] = [];
          }

          if (this.hasOwnProperty('firstName') && this.hasOwnProperty('lastName')) {
            creatorObject['given'] = this.firstName;
            creatorObject['family'] = this.lastName;
          } else {
            creatorObject['literal'] = this.name;
          }

          cslObject[cslCreatorKey].push(creatorObject);
        });
        break;

      case 'date':
        cslObject['issued'] = {'raw': val}
        break;
        
      default:
        fieldKey = $typeMap
                     .find('field[value="' + key + '"]')
                     .attr('baseField') || key;
        cslKey = $cslFieldMap
                   .find('fieldMap[zfield="' + fieldKey + '"]')
                   .attr('cslField');
        cslObject[cslKey] = val;
      }
    });

    return cslObject;
  };

  zoteroFormToObject = function($form, sorted) {
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

  initArchiveAutocomplete = function() {
    $('[data-zotero-key="archive"] textarea').autocomplete({
      source: function(request, response) {
        $.getJSON('/api/document/archives/',{'q': request.term}, function(data) {
          response($.map(data, function(item, index) {
            return { label: item.name };
          }));
        });
      }
    });
  }

  // do this on page load
  initArchiveAutocomplete();

  // Bindings
  $('#zotero-information-edit')
    // Get form on creator type change
    .on('change', 'select[name="item-type-select"]', function() {
      var $itemTypeSelect = $(this),
        $zoteroContainer = $itemTypeSelect.parents('#zotero-information-edit'),
        itemType = $itemTypeSelect.val();
      if (itemType.length) {
        $.ajax({
          url: '/api/document/template/',
          data: {'itemType': itemType},
          success: function(data) {
            $zoteroContainer.data('itemTypeSelect', $itemTypeSelect.parents('.control-group'));

            $zoteroContainer
              .html($(data).closest('#zotero-information-edit').html())
              .find('.zotero-entry-delete').remove();
        
            initArchiveAutocomplete();
          }
        });
      }
    })

    // Update creators' hidden inputs as they're changed
    .on('input change', '.zotero-creator', function() {
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
    })

    // Update form data on input & change
    .on('input change', function() {
      var $this = $(this),
        zoteroObject = zoteroFormToObject($this);
      $this
        .data('asZoteroObject', zoteroObject)
        .data('asCslObject', zoteroObjectToCsl(zoteroObject));
    });

});
