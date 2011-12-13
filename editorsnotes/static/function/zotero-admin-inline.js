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
    return JSON.stringify(zoteroDataObject);
  }
  
  var json_to_reference = function() {
    var zoteroJSON = buildZoteroJson();
    $.ajax({
      url: '/api/document/csl/',
      data: {'zotero-json' : zoteroJSON},
      success: function(data){
        var formattedRef = runCite(JSON.stringify(data));

        var wymconfig = {
          skin: 'custom',
          toolsItems: [
            {'name': 'Bold', 'title': 'Strong', 'css': 'wym_tools_strong'}, 
            {'name': 'Italic', 'title': 'Emphasis', 'css': 'wym_tools_emphasis'},
            {'name': 'InsertOrderedList', 'title': 'Ordered_List', 'css': 'wym_tools_ordered_list'},
            {'name': 'InsertUnorderedList', 'title': 'Unordered_List', 'css': 'wym_tools_unordered_list'},
            {'name': 'Undo', 'title': 'Undo', 'css': 'wym_tools_undo'},
            {'name': 'Redo', 'title': 'Redo', 'css': 'wym_tools_redo'},
            {'name': 'CreateLink', 'title': 'Link', 'css': 'wym_tools_link'},
            {'name': 'Unlink', 'title': 'Unlink', 'css': 'wym_tools_unlink'},
            {'name': 'ToggleHtml', 'title': 'HTML', 'css': 'wym_tools_html'}
          ],
          updateSelector: 'input:submit',
          updateEvent: 'click',
          classesHtml: ''
        };

        var $textArea = $('#id_description');
        $textArea.siblings('div.wym_box').remove();
        $textArea.text(formattedRef);
        $textArea.wymeditor(wymconfig);
      }
    });
  }

  var generateLink = '<a href="#_" id="generate-citation">Generate from Zotero information</a>'
  $('#id_description').parent().append(generateLink);

  $('#generate-citation').live('click', function() {
    json_to_reference();
  });

  //
  // For dealing with contributor types
  //

  $('select.creator-select').live('click', function() {
    $creatorSelect = $(this);
    if (!$creatorSelect.hasClass('creators-select-queried')) {
      var itemType = $(this).closest('.zotero-entry').siblings('[zotero-key="itemType"]')
        .find('input[type="hidden"]').val();
      $creatorSelect.children().hide();
      $.ajax({
        url: '/api/document/creators/',
        data: {'itemType' : itemType},
        success: function(data) {
          $creatorSelect.children().remove();
          $.each(data, function(index, creatorType) {
            var creatorOption = $('<option>' + creatorType.localized + '</option>')
              .val(creatorType.creatorType);
            $creatorSelect.append(creatorOption);
            $creatorSelect.addClass('creators-select-queried');
          });
        }
      });
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
