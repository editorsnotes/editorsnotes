$(document).ready(function(){
  var renderInlineForm = function(zoteroString) {
    var itemTypeSrc = $('#item-type-template').html(),
      creatorsSrc = $('#creators-template').html(),
      tagsSrc = $('#tags-template').html(),
      baseSrc = $('#base-template').html(),
      itemTypeTemplate = Handlebars.compile(itemTypeSrc),
      creatorsTemplate = Handlebars.compile(creatorsSrc),
      tagsTemplate = Handlebars.compile(tagsSrc),
      baseTemplate = Handlebars.compile(baseSrc);

    Handlebars.registerHelper('localized', function(key) {
      return zoteroLocalization[key];
    });
    Handlebars.registerHelper('stringify', function(str) {
      return JSON.stringify(str);
    });

    var initZoteroForm = function () {
      var zoteroData = JSON.parse(zoteroString),
      $table = $('<div class="modal" id="myModal"><table><tbody>'),
      $tbody = $table.find('tbody');

      $.each(zoteroData, function(key, val){
        switch (key) {
          case 'itemType':
            $tbody.append(itemTypeTemplate(zoteroData));
            break;

          case 'creators':
            $tbody.append(creatorsTemplate(zoteroData));
            break;

          case 'tags':
            $tbody.append(tagsTemplate(zoteroData));
            break;

          default:
            var fieldData = {'key': key, 'val': val};
            $tbody.append(baseTemplate(fieldData));
            break;
        }
      });
      $tbody.append( $('<input type="hidden">').val(zoteroString) );
      return $table;
    }
    return initZoteroForm();
  }
  $('.edit-button').click(function(event){
    $.get('/document/templates/', function(data) {
      $('body').append(data);
      var a = $('#zotero-data-here').val();
      var $x = renderInlineForm(a);
      $x.modal().css({
        'width': '800px',
        'margin-left': function() {
          return -($(this).width() / 2);
        }
      });
    });
  });

});
