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
        update_creator_values();
        var creatorsArray = new Array;
        var $creators = $field.children('.zotero-creator');
        $.each($field.children('.zotero-creator'), function(key, val){
          var $creatorInput = $(val).children('input').val();
          var creatorObject = JSON.parse($creatorInput);
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
        var textArea = $.wymeditors(0);
        if ( !$cachedInput.hasClass('cached') ) {
          $cachedInput.val(textArea.html()).addClass('cached');
          $restorePrompt.show();
        }
        textArea.html(formattedRef);
      }
    });
  }

  var generateLink = '<a href="#_" id="generate-citation">Generate from Zotero information</a>';
  var $restorePrompt = $('<a href="#_" id="restore-original-citation">(restore original)</a>')
    .css({'color' : 'red', 'display' : 'none'});
  var $cachedInput = $('<input id="cached-citation" type="hidden">');
  $('#id_description').parent().append(generateLink, ' ', $restorePrompt, $cachedInput);

  $('#generate-citation').live('click', function() {
    json_to_reference();
  });

  $restorePrompt.click(function() {
    $.wymeditors(0).html($cachedInput.val());
  });

  //
  // For dealing with contributor types
  //

  var update_creator_values = function() {
    $.each($('.zotero-creator'), function(key, value) {
      var $creator = $(this);
      var $creatorInput = $creator.find('input[type="hidden"]');
      var creatorObject = new Object;
      $.each($creator.children('.creator-attr'), function(attrKey, attrVal) {
        $attribute = $(this);
        creatorObject[$attribute.attr('creator-key')] = $attribute.val();
      });
      creatorObject['creatorType'] = $creator.attr('creator-type');
      $creatorInput.val(JSON.stringify(creatorObject));
    });
  }

  // Change hidden input whenver creator is changed
  $('.zotero-creator textarea').live('keyup paste', function() {
    update_creator_values();
  });

  // Initialize cache in global scope
  zoteroCreatorsCache = new Object;

  $('select.creator-select').live('click', function() {
    var $creatorSelect = $(this);
    if (!$creatorSelect.hasClass('creators-select-queried')) {
      var itemType = $(this).closest('.zotero-entry').siblings('[zotero-key="itemType"]')
        .find('input[type="hidden"]').val();
      $creatorSelect.children().hide();
      $creatorSelect.append('<option id="creators-loading">Loading...</option>');
      if (zoteroCreatorsCache[itemType] == undefined) {
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
            zoteroCreatorsCache[itemType] = $creatorSelect;
          },
          error: function() {
            alert('Error connecting to Zotero server');
          }
        });
      }
      else {
        var replacementList = zoteroCreatorsCache[itemType].clone();
        $creatorSelect.html(replacementList.children());
        $creatorSelect.addClass('creators-select-queried');
      }
    }
  });

  $('select.creator-select').live('change', function() {
    var $creatorSelect = $(this);
    var selectedCreatorType = $(this).children('option:selected').val();
    $creatorSelect.parent().attr('creator-type', selectedCreatorType);
  });

  $('.creator-add').live('click', function() {
    var $newCreator = $(this).parent().clone();
    $newCreator.find('textarea').val('');
    $newCreator.insertAfter($(this).parent());
  });

  $('.creator-remove').live('click', function() {
    $(this).parent().remove();
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
