$(document).ready(function(){
  var templates = {};

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

  Handlebars.registerHelper('localized', function(key) {
    return zoteroLocalization[key];
  });
  Handlebars.registerHelper('stringify', function(str) {
    return JSON.stringify(str);
  });

  var modal = '<div id="document-inline-edit" class="modal">' +
                '<h3>Add a document</h3>' +
                '<textarea id="document-description-edit"></textarea>' +
                '<hr>' +
                '<div id="document-zotero-information">' +
                '</div>' +
                '<hr>' +
                '<div style="margin-bottom: 8px;">' +
                  '<a id="document-edit-close" class="btn btn-danger">Cancel</a>' +
                  '<a class="btn btn-primary pull-right">Save</a>' +
                '</div>' +
              '</div>';

  var $modal = $(modal).hide().appendTo($('body'));
  $modal.find('#document-description-edit').wymeditor({
    skin: 'custom',
    toolsItems: [
      {'name': 'Bold', 'title': 'Strong', 'css': 'wym_tools_strong'}, 
      {'name': 'Italic', 'title': 'Emphasis', 'css': 'wym_tools_emphasis'},
    ],
    updateSelector: 'input:submit',
    updateEvent: 'click',
    classHtml: ''
  });

  var buildZoteroForm = function (zoteroString) {
    if (zoteroString.length < 2) {
      return templates.itemTypeSelect
    } else {
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
  }


  $('#add-document-modal').live('click', function(){
    $.get('/document/templates/', function(data) {
      $('body').append(data);
      if (!templates.length) {
        templates = initTemplates();
      }

      $modal
        .modal({backdrop: 'static'}).css({
          'width': '800px',
          'margin-left': function() {
            return -($(this).width() / 2);
          }
        })
        .find('#document-zotero-information')
          .html('').append(buildZoteroForm(''));
    });
  });

  $('#document-edit-close').live('click', function(){
    $modal.modal('hide');
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

});
