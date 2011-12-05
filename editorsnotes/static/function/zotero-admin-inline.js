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
});
