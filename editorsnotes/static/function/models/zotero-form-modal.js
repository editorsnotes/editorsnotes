$(document).ready(function(){
  var templates = {},
    creatorsCache = {};

  /****************************************************************************
   Helper functions without side effects
   ****************************************************************************/
  var initTemplates = function() {
    var typeSelectSrc = $('#item-type-select-template').clone().html(),
      itemTypeSrc = $('#item-type-template').html(),
      creatorsSrc = $('#creators-template').html(),
      tagsSrc = $('#tags-template').html(),
      baseSrc = $('#base-template').html(),
      t = {};
    t.itemTypeSelect = typeSelectSrc;
    t.itemTypeTemplate = Handlebars.compile(itemTypeSrc);
    t.creatorsTemplate = Handlebars.compile(creatorsSrc);
    t.tagsTemplate = Handlebars.compile(tagsSrc);
    t.baseTemplate = Handlebars.compile(baseSrc);
    return t;
  };

  var buildZoteroForm = function (zoteroString) {
    var zoteroData = JSON.parse(zoteroString),
      $table = $('<table><tbody>');
      $tbody = $table.find('tbody');

    $.each(zoteroData, function(key, val){
      switch (key) {
        case 'itemType':
          $tbody.append(templates.itemTypeTemplate(zoteroData));
          break;

        case 'creators':
          $tbody.append(templates.creatorsTemplate(zoteroData));
          break;

        case 'tags':
          $tbody.append(templates.tagsTemplate(zoteroData));
          break;

        default:
          var fieldData = {'key': key, 'val': val};
          $tbody.append(templates.baseTemplate(fieldData));
          break;
      }
    });
    $tbody.append( $('<input type="hidden">').val(zoteroString) );
    return $table;
  }

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

  /***************************************************************************
    Everything else
   ***************************************************************************/

  var updateCreatorValues = function() {
    // Update the inputs in zotero creator fields
    $.each( $('.zotero-creator'), function() {
      var $creator = $(this),
        creatorObject = {};
      $.each( $creator.find('.creator-attr'), function() {
        var $attr = $(this);
        creatorObject[$attr.data('creator-key')] = $attr.val();
      });
      $creator
        .find('input[type="hidden"]')
        .val( JSON.stringify(creatorObject) );
    });
  }

  Handlebars.registerHelper('localized', function(key) {
    return zoteroLocalization[key];
  });
  Handlebars.registerHelper('stringify', function(str) {
    return JSON.stringify(str);
  });

  var modal = '<div id="document-inline-edit" class="modal">' +
                '<div id="document-description">' + 
                  '<h3>Add a document</h3>' +
                  '<textarea id="document-description-edit"></textarea>' +
                '</div>' +
                '<div id="document-zotero-information">' +
                '</div>' +
                '<div id="modal-edit-row">' +
                  '<a id="document-edit-close" class="btn btn-danger">Cancel</a>' +
                  '<a id="document-save" class="btn btn-primary pull-right">Save</a>' +
                '</div>' +
              '</div>';

  var $modal = $(modal).hide().appendTo($('body')),
    $documentwym;
  $modal.find('#document-description-edit').wymeditor({
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
      $documentwym = this;
      $($documentwym._iframe).css('height', '92px');
      var generateCiteLink = '' +
          '<a style="width: 100px;" id="generate-citation" href="#_">Generate citation</a>'
      $(this._box).find(this._options.toolsSelector + this._options.toolsListSelector)
        .append(generateCiteLink);
    }
  });



  /***************************************************************************
   * Bindings
   ***************************************************************************/
  $('#add-document-modal').live('click', function(){
    $.get('/document/templates/', function(data) {
      $('body').append(data);
      if (!templates.length) {
        templates = initTemplates();
      }
      $documentwym.html('');

      $modal
        .modal({backdrop: 'static'}).css({
          'width': '800px',
          'top': '45%',
          'margin-left': function() {
            return -($(this).width() / 2);
          }
        })
        .find('#document-zotero-information')
          .html('').append(templates.itemTypeSelect);
    });
  });

  $('#document-edit-close').live('click', function(){
    $modal.modal('hide');
  });

  $('#document-save').live('click', function() {
    var zoteroForm = $('#document-zotero-information table');
    updateCreatorValues();

    $.ajax({
      type: 'POST',
      url: '/document/add/',
      data: {
        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
        'zotero-string': JSON.stringify( zoteroFormToObject(zoteroForm, true) ),
        'document-description': $documentwym.html()
      },
      success: function(data) {
        var doc = JSON.parse(data);
        $('#add-section input.ui-autocomplete-input').val(doc.document);
        $('#id_document').val(doc.id);
        $modal.modal('hide');
      }
    });
  });

  $('select[name="item-type-select"]').live('change', function() {
    var selectedItemType = $(this).val();
    if (selectedItemType.length) {
      $.ajax({
        url: '/api/document/blank/',
        data: {'itemType': selectedItemType, 'type': 'json'},
        success: function(data) {
          $modal.find('#document-zotero-information')
            .html('')
            .append(buildZoteroForm(data));
        }
      });
    }
  });

  $('.creator-select.not-queried').live('click', function() {
    var $creatorSelect = $(this);
    var selectedItemType = $creatorSelect
                         .parents('#document-zotero-information')
                         .find('[data-zotero-key="itemType"] input[type="hidden"]')
                         .val();
    var replaceCreatorTypes = function(c) {
      $creatorSelect.removeClass('not-queried').children().remove();
      $.each(c, function() {
        var $opt = $('<option>').val(this.creatorType).text(this.localized);
        $creatorSelect.append($opt);
      });
    };

    if (!creatorsCache[selectedItemType]) {
      $.ajax({
        url: '/api/document/creators/',
        data: {'itemType': selectedItemType},
        success: function(data) {
          replaceCreatorTypes(data);
          creatorsCache[selectedItemType] = data;
        }
      });
    } else {
      replaceCreatorTypes(creatorsCache[selectedItemType]);
    }
  });

  $('.add-creator').live('click', function() {
    var $oldCreator = $(this).parents('tr'),
      $newCreator = $oldCreator.clone().insertAfter($oldCreator);
    $newCreator.find('textarea').val('');
  });

  $('.remove-creator').live('click', function() {
    var $thisRow = $(this).parents('tr');
    if ($thisRow.siblings('.zotero-creator').length) {
      $thisRow.remove();
    }
  });

  $('#generate-citation').live('click', function() {
    var zoteroForm = $('#document-zotero-information table'),
      zoteroString;
    updateCreatorValues();
    zoteroString = JSON.stringify( zoteroFormToObject(zoteroForm) );
    $.ajax({
      url: '/api/document/csl/',
      data: {'zotero-json': zoteroString},
      success: function(data) {
        var formattedRef = runCite( JSON.stringify(data) );
        $documentwym.html(formattedRef);
      }
    });

  });

});
