
  Handlebars.registerHelper('localized', function(key) {
    return zoteroLocalization[key];
  });
  Handlebars.registerHelper('stringify', function(str) {
    return JSON.stringify(str);
  });

  var initTemplates = function() {
    var t = {},
      typeSelectSrc = $('#item-type-select-template').html(),
      itemTypeSrc = $('#item-type-template').html(),
      creatorsSrc = $('#creators-template').html(),
      tagsSrc = $('#tags-template').html(),
      baseSrc = $('#base-template').html(),
      rebuildDelimiters = function(t) {
        // Needed because Django does not allow "raw" templates
        return t.replace('((', '{{', 'g').replace('))', '}}', 'g');
      };
    t.itemTypeSelect = typeSelectSrc;
    t.itemTypeTemplate = Handlebars.compile(rebuildDelimiters(itemTypeSrc));
    t.creatorsTemplate = Handlebars.compile(rebuildDelimiters(creatorsSrc));
    t.tagsTemplate = Handlebars.compile(rebuildDelimiters(tagsSrc));
    t.baseTemplate = Handlebars.compile(rebuildDelimiters(baseSrc));
    return t;
  };

  var buildZoteroForm = function (zoteroString) {
    var zoteroData,
      $table = $('<table class="zotero-information"><tbody>'),
      $tbody = $table.find('tbody'),
      templates = initTemplates();

    if (!zoteroString) {
      var itemTypeSelect = $(templates.itemTypeSelect);
      itemTypeSelect.find('select[name="item-type-select"]').change(function() {
        var selectedItemType = $(this).val();
        if (selectedItemType.length) {
          $.ajax({
            url: '/api/document/template/',
            data: {
              'itemType': selectedItemType,
              'templateFor': 'item'
            },
            success: function(data) {
              var $zoteroTable = buildZoteroForm(data).insertAfter(itemTypeSelect);
              itemTypeSelect.remove();
            }
          });
        }
      });
      return itemTypeSelect;
    }

    if (typeof(zoteroString) == 'string') {
      zoteroData = JSON.parse(zoteroString)
    } else {
      zoteroData = zoteroString;
    }
    $.each(zoteroData, function(key, val){
      switch (key) {
        case 'itemType':
          $tbody.append(templates.itemTypeTemplate(zoteroData));
          break;

        case 'creators':
          var $creators = $(templates.creatorsTemplate(zoteroData)).appendTo($tbody);

          // Binding for getting creator types
          $creators.find('.creator-select').each(function() {
            $(this).click(function() {
              if (!$(this).hasClass('not-queried')) {
                return true;
              }
              var $creatorSelect = $(this),
                $zoteroTable = $(this).parents('table'),
                selectedItemType,
                replaceCreatorTypes;

              selectedItemType = $zoteroTable.find('[data-zotero-key="itemType"] input').val();
              replaceCreatorTypes = function(c) {
                $creatorSelect.removeClass('not-queried').children().remove();
                $.each(c, function() {
                  var $opt = $('<option>').val(this.creatorType).text(this.localized);
                  $creatorSelect.append($opt);
                });
              };

              if (!$zoteroTable.data('creatorsCache')) {
                $zoteroTable.data('creatorsCache', {});
              }

              if (!$zoteroTable.data('creatorsCache')[selectedItemType]) {
                //$loader.show();
                $.ajax({
                  url: '/api/document/template/',
                  data: {
                    'itemType': selectedItemType,
                    'templateFor': 'creators'
                  },
                  success: function(data) {
                    //$loader.hide();
                    replaceCreatorTypes(data);
                    $zoteroTable.data('creatorsCache')[selectedItemType] = data;
                  }
                });
              } else {
                replaceCreatorTypes($zoteroTable.data('creatorsCache')[selectedItemType]);
              }
            });
          });

          // Binding for adding/removing creators
          $creators.find('.add-creator').each(function() {
            $(this).click(function() {
              var $oldCreator = $(this).parents('tr'),
                $newCreator = $oldCreator.clone(true, true).insertAfter($oldCreator);
              $newCreator.find('textarea').val('');
            });
          });

          $creators.find('.remove-creator').each(function() {
            $(this).click(function() {
              var $thisRow = $(this).parents('tr');
              if ($thisRow.siblings('.zotero-creator').length) {
                $thisRow.remove();
              }
            });
          });

          $creators.find('textarea').each(function() {
            $(this).bind('change keyup input', function() {
              var $creator = $(this).parents('.zotero-creator'),
                creatorObject = {};
              $creator.find('.creator-attr').each(function() {
                var $attr = $(this);
                creatorObject[$attr.data('creator-key')] = $attr.val();
              });
              $creator
                .find('input[type="hidden"]')
                .val( JSON.stringify(creatorObject) );
            });
          });

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
        generateCiteLink.click(function() {
          var zoteroForm = $('table.zotero-information'),
            zoteroString;
          if (!zoteroForm.length) {
            alert('Fill in zotero information to generate citation');
            return true;
          }
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
      $(this._box).find(this._options.toolsSelector + this._options.toolsListSelector)
        .append(generateCiteLink);
      }
    }
