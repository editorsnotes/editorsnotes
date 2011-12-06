$(document).ready(function() {
  var buildZoteroJson = function() {
    var zoteroDataObject = new Object;
    var fields = $('.zotero-entry');
    $.each(fields, function(key, val) {
      var $field = $(val);
      var fieldKey = $field.attr('zotero-key');
      if (fieldKey == 'itemType'){
      }
      else if (fieldKey == 'creators'){
        var creatorsArray = new Array;
        var $creators = $field.children('.zotero-creator');
        $.each($creators, function(key, val){
          var creatorObject = new Object;
          var $creator = $(val);
          var creatorNameParts = $creator.children('.creator-attr');
          creatorObject.creatorType = $creator.attr('creator-type');
          $.each(creatorNameParts, function(key, name){
            var $namePart = $(name);
            creatorObject[$namePart.attr('creator-key')] = $namePart.val();
          });
          creatorsArray.push(creatorObject);
        });
        zoteroDataObject['creators'] = creatorsArray;
      }
      else if (fieldKey == 'tags'){
      }
      else {
        var fieldVal = $field.children('textarea');
        zoteroDataObject[fieldKey] = fieldVal.val()
      }
    });
    return zoteroDataObject;
  }

  var getItemTemplate = function(itemType) {
    $.ajax({
      url: '/document/blank/',
      data: {'itemType' : itemType},
      success: function(data){return data},
      error: function(){return false}
    });
  };

  $('#zotero-item-type-select').change(function() {
    var $selector = $(this);
    var $container = $selector.parent('#zotero-information');
    if ($selector.val() != '') {
      var itemType = $selector.val();
      $container.children().hide();
      $container.append('<div id="zotero-loading">Loading...</div>');
      $.ajax({
        url: '/document/blank/',
        data: {'itemType' : itemType},
        success: function(data){
          $container.replaceWith(data);
        },
        error: function(){
          $('#zotero-loading').html('<p>Error getting new item template</p>');
          $container.children().show();
        }
      });
    }
  });

});
