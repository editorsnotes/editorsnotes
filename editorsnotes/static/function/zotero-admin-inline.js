$(document).ready(function() {

  var buildZoteroJson = function() {
    var zoteroDataObject = new Object;
    var fields = $('.zotero-entry');
    $.each(fields, function(key, val) {
      var $field = $(val);
      var fieldKey = $field.attr('zotero-key');
      if (fieldKey == 'itemType'){
        zoteroDataObject['itemType'] = $field.find('input[type="hidden"]').val();
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
  
  console.log(buildZoteroJson());
  $.ajax({
    url: '/api/document/csl/',
    data: {'zotero-json' : JSON.stringify(buildZoteroJson())},
    success: function(data){
      console.log(runCite(JSON.stringify(data)));
      console.log(data);
    },
    error: function(){
      console.log('error');
    }
  });

  // Cache values entered into the form if (for example) itemType is changed.
  var zoteroDataCache = new Object;

  $('#zotero-item-type-select').live('change', function() {
    var $selector = $(this);
    var $container = $selector.closest('#zotero-information');
    if ($selector.val() != '') {

      // Store form values in cache
      $.each($container.children('.zotero-entry'), function(key, value) {
        var $entry = $(value);
        var zoteroKey = $entry.attr('zotero-key');
        if (zoteroKey == 'itemType' ){
        }
        else if (zoteroKey == 'creators'){
        }
        else if (zoteroKey == 'tags'){
        }
        else {
          data = $entry.find('textarea').val();
          if ( data != '' ) {
            zoteroDataCache[zoteroKey] = data;
          }
        }
      });

      var itemType = $selector.val();
      $container.children().hide();
      $container.append('<div id="zotero-loading">Loading...</div>');
      $.ajax({
        url: '/api/document/blank/',
        data: {'itemType' : itemType},
        success: function(data){
          $container.replaceWith(data);
          //TODO: pop data cache into new form
        },
        error: function(){
          $('#zotero-loading').html('<p>Error getting new item template</p>');
          $container.children().show();
        }
      });
    }
  });

  $('#zotero-change-item-type').live('click', function() {
    $('#zotero-item-type-list').show();
  });

});
