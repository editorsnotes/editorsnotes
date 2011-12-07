$(document).ready(function() {
  
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
        url: '/document/blank/',
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
