$(document).ready(function(){
  var csrf_token = $("input[name='csrfmiddlewaretoken']").attr('value');
  
  $(".collection-item").live('click', function(){
    $(this).parent().children().removeClass('collection-selected');
    $(this).addClass('collection-selected');
    var $itemsContainer = $('#items');
    var $loader = $itemsContainer.find('.loader');
    var $table = $itemsContainer.find('#items-table');
    
    $table.hide();
    $loader.show();
    $('#item-list').html('');
    
    var selectedSource = $(this).attr('location');

    $('.items-option').each(function() {
      var optVal = $(this).val()
      var optKey = $(this).parent().attr('key')
      if ( optVal != '' ) {
        queryOptions[optKey] = optVal
      }
    });
    var afterLoad = function() {
      $loader.hide();
      $table.show();
      $itemsContainer.attr({'location' : selectedSource});
    }
    var queryOptions = { 'start' : 0, 'limit' : pageInterval, 'order' : 'dateModified', 'sort' : 'desc' }
    loadItems(selectedSource, queryOptions, afterLoad);
  });
  
  $('#zotero-search-submit').click(function() {
    var $itemsContainer = $('#items');
    var $loader = $itemsContainer.find('.loader');
    var $table = $itemsContainer.find('#items-table');
    
    $table.hide();
    $loader.show();
    $('#item-list').html('');
    
    var selectedSource = $itemsContainer.attr('location');

    $('.items-option').each(function() {
      var optVal = $(this).val()
      var optKey = $(this).parent().attr('key')
      if ( optVal != '' ) {
        queryOptions[optKey] = optVal
      }
    });
    var afterLoad = function() {
      $loader.hide();
      $table.show();
    }
    var query = $('#zotero-search').attr('value');
    var queryOptions = { 'start' : 0, 'limit' : pageInterval, 'order' : 'dateModified', 'sort' : 'desc', 'q' : encodeURIComponent(query) }
    loadItems(selectedSource, queryOptions, afterLoad);
    $('#zotero-search').attr('value', '');
  });
  
  // 4. Post selected items
  $('#post-items').click(function(){
    $(this).append('<img src="/media/style/icons/ajax-loader.gif">');
    var selectedItems = $('input:checked').parents('tr').children('span')
    var itemsArray = new Array
    $.each(selectedItems, function(key, value) {
      itemsArray.push($(value).text())
    });
    $.post("import/",
      {'items' : itemsArray, 'csrfmiddlewaretoken': csrf_token},
      function (response) {
        var results = JSON.parse(response)
        $.each(results['existing_docs'], function(key, value) {
          $("#not-imported").append($('<li>').append(value));
        });
        $.each(results['imported_docs'], function(key, value) {
          $("#imported").append($('<li>').append(value));
        });
        $('#items').hide();
        $('#query').hide();
        $('#success').show();
      }
    );
  });

  // 5. Allow Zotero items to be linked to already existing documents
  $("#doc-add-form").dialog({
    autoOpen: false,
    modal: true,
    width: 500,
    title: 'Connect to existing document'
  });
  $('.add-to-document').live('click', function(){
    var link = $(this).parent()
    $('#document')
      .html(link.find('.zotero-object')[0].text)
      .attr('source', link.attr('id'))
      .attr('value', link.find('input').attr('value'));
    $("#doc-add-form").dialog('open');
  });
  $('#docsearch input')
    .autocomplete({
      source: function(request, response) {
        $.getJSON('/api/documents/', { q: request.term }, function(data) {
          response($.map(data, function(item, index) {
            return { label: item.description, id: item.id };
          }));
        });
      },
      minLength: 3,
      select: function(event, ui) {
        if (ui.item) {
          $('#link-document').show()
            .attr('document', ui.item.id);
        }
      }
  });
  $('#link-document').click(function(){
    $.post("update_link/",
      {
        'doc_id' : $(this).attr('document'),
        'zotero_info' : $('#document').attr('value'),
        'csrfmiddlewaretoken': csrf_token
      },
      function(data) {
        var old_div = $('#document').attr('source');
        $('#' + old_div ).remove();
        $('#docsearch input')[0].value = "";
        $("#doc-add-form").dialog('close');
      }
    );
  });

  

// Ajax calls
  var loadCollections = function (libraryURL) {
    $.getJSON('collections/', {'loc' : libraryURL }, function(data) {
      var i = 1
      var $collectionList = $('#collections')
      $.each(data.collections, function (key, value) {
        var collection = $('<li>')
          .attr({
            'class' : 'collection-item',
            'location' : value.location,
            'id' : 'collection-' + i
          })
          .text(value.title);
        $collectionList.append(collection);
        i++
      });
    });
  };

  var loadItems = function(loc, opts, onSuccess) {
    $.getJSON('items/', {'loc' : loc, 'opts' : JSON.stringify(opts) }, function(data) {
      var i = opts['start'] + 1
      var start = i;
      var totalItems = data.total_items;
      $.each(data.items, function (key, value) {
        var itemData = {
          'json' : value.item_json,
          'url' : value.url,
          'date' : dateParser.parse(value.date),
          'citation' : runCite(value.item_csl),
          'related_object' : related_object,
          'related_id' : related_id
        }
        var itemRow = $('<tr>').attr({
          'class' : 'item',
          'id' : 'zotero-item-' + i
        });
        itemRow.append($('<span>').attr('item', 'zotero-item-' + i).text(JSON.stringify(itemData)).hide())
        var zoteroData = JSON.parse(value.item_json);
        function parseCreators(creators) {
          var parsedCreators = new Array;
          creators.forEach(function(creator) {
            parsedCreators.push(creator.lastName)
          });
          return parsedCreators.join(', ');
        };
        function parseItemType(itemType) {
          return string.charAt(0).toUpperCase() + string.slice(1);
        }
        itemRow.append('<td class="item-checkbox"><label><input type="checkbox"></label></td>');
        var tableData = [value.title, parseCreators(zoteroData.creators), value.date, value.item_type]
        $.each(tableData, function(index, data) {
          itemRow.append('<td>' + data + '</td>')
        });
        $('#item-list').append(itemRow);
        i++
      });
      updateCounter(start, totalItems);
      onSuccess();
    });
  }


  var pageInterval = 25;
  var $itemsCount = $('#items-browsing-count');
  var updateCounter = function(initial, total) {
    var start = initial;
    if (start + pageInterval < total) {
      var end = start + pageInterval - 1;
    }
    else {
      var end = total;
    }
    $itemsCount.html('Viewing items ' + start + '-' + end + ' of ' + total)
  }
    
  // Get collections on page load

  loadCollections(zoteroLibrary)
  
});
