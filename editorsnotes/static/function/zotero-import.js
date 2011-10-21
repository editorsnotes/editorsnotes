$(document).ready(function(){
  var csrf_token = $("input[name='csrfmiddlewaretoken']").attr('value');
  
  $(".collection-item").live('click', function(){
    $(this).parent().children().removeClass('collection-selected');
    $(this).addClass('collection-selected');

    var loaderContainer = $('#items-loading');
    var itemsTable = $('#items-table');
    var selectedSource = $(this).attr('location');
    
    itemsTable.hide();
    $('#item-list').html('');

    var queryOptions = {}
    loadItems(selectedSource, queryOptions, itemsTable, loaderContainer);
  });
  
  $('#zotero-search-submit').click(function() {
    var loaderContainer = $('#items-loading');
    var itemsTable = $('#items-table');
    var selectedSource = $(this).attr('location');
    
    itemsTable.hide();
    $('#item-list').html('');
    
    var selectedSource = itemsTable.attr('location');
    var query = $('#zotero-search').attr('value');
    var queryOptions = {'q' : encodeURIComponent(query)}
    loadItems(selectedSource, queryOptions, itemsTable, loaderContainer);
    $('#zotero-search').attr('value', '');
  });
  
  $('#items-continue').click(function() {
    var selectedItems = $('input:checked').parents('tr').children('input')
    $.each(selectedItems, function(counter, data) {
      var itemData = JSON.parse($(data).attr('value'));
      var newContainer = $('<div>').append(data).append(itemData['citation']);
      /*
      var relatedTopics = $('<ul class="related-topics">').html('<h6>Related Topics:</h6>');
      if ( itemData.tags.length > 0 ) {
        var tags = itemData.tags
        $.each(tags, function(counter, data) {
          $.getJSON('/api/topics/', {'q' : data.tag.replace(/\./g, ' ') }, function(data) {
            if (data.length > 0) {
              var topic = $('<li>').attr({ 'class' : 'related-topic', 'rel_id' : data[0].id }).text(data[0].preferred_name);
              relatedTopics.append(topic);
            }
          });
        });
      }
      if ( related_object != '' ) {
        relatedTopics.append('<li class="related-topic" rel_id="' + related_id + '">Topic referral</li>');
      }
      newContainer.append(relatedTopics).append(data);
      */
      $('#items-to-post').append(newContainer)
    });
    $('#browse').hide();
    $('#continue').show();
  });
  
  
  // 4. Post selected items
  $('#post-items-submit').click(function(){
    $(this).hide();
    loader = $(this).next();
    loader.html('<img class="loader" src="/media/style/icons/ajax-loader.gif">').show();
    var selectedItems = $('#items-to-post div input')
    var itemsArray = new Array
    $.each(selectedItems, function(key, item) {
      itemsArray.push($(item).attr('value'));
    });
    $.post("import/",
      {'items' : itemsArray, 'csrfmiddlewaretoken': csrf_token},
      function (response) {
        var results = response;
        loader.html('<p style="color: red;">Items sucessfully imported.</p>');
        $('#post-items-success').show();
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
  var loadCollections = function (libraryURL, collectionContainer, loaderContainer) {
    loaderContainer.html('Loading collections... <img class="loader" src="/media/style/icons/ajax-loader.gif">').show();
    $.getJSON('collections/', {'loc' : libraryURL }, function(data) {
      var i = 1
      $.each(data.collections, function (key, value) {
        var collection = $('<li>')
          .attr({
            'class' : 'collection-item',
            'location' : value.location,
            'id' : 'collection-' + i
          })
          .text(value.title);
        collectionContainer.append(collection);
        i++
      });
      loaderContainer.hide();
      collectionContainer.show();
    })
    .error(function() {
      loaderContainer.html('<p>Error reaching Zotero server.<p><a href="#" class="button" id="load-collections-retry">Retry</a>').show();
    });
  };

  var loadItems = function(sourceLocation, opts, itemsContainer, loaderContainer) {
    loaderContainer.html('Loading items... <img class="loader" src="/media/style/icons/ajax-loader.gif">').show();
    var itemList = itemsContainer.find('#item-list');
    var buildQueryOptions = function (options) {
      var newOptions = {'start' : 0,
                        'limit' : pageInterval,
                        'order' : 'dateModified',
                        'sort' : 'desc'}
      $.each(options, function (key, value) {
        newOptions[key] = value;
      });
      return newOptions;
    }
    var queryOptions = buildQueryOptions(opts);
    $.getJSON('items/', {'loc' : sourceLocation, 'opts' : JSON.stringify(queryOptions) }, function(data) {
      var i = queryOptions['start'] + 1
      var start = i;
      var totalItems = data.total_items;
      $.each(data.items, function (key, value) {
        var zoteroData = JSON.parse(value.item_json);
        var itemData = {
          'json' : value.item_json,
          'url' : value.url,
          'date' : dateParser.parse(value.date),
          'citation' : runCite(value.item_csl),
          'tags' : zoteroData['tags']
        }
        var itemRow = $('<tr>').attr({'class' : 'item', 'id' : 'zotero-item-' + i});
        var itemInformation = $('<input>')
          .attr({'item' : ('zotero-item-' + i),
                 'type' : 'hidden',
                 'value' : JSON.stringify(itemData)});
        itemRow.append(itemInformation);
        itemRow.append('<td class="item-checkbox"><label><input type="checkbox"></label></td>');
        var parseCreators = function(creators) {
          var parsedCreators = new Array;
          creators.forEach(function(creator) {
            parsedCreators.push(creator.lastName)
          });
          return parsedCreators.join(', ');
        };
        var parseItemType = function(itemType) {
          return string.charAt(0).toUpperCase() + string.slice(1);
        }
        var tableData = [value.title, parseCreators(zoteroData.creators), value.date, value.item_type]
        $.each(tableData, function(index, data) {
          itemRow.append('<td>' + data + '</td>')
        });
        itemList.append(itemRow);
        i++
      });
      updateCounter(start, totalItems);
      loaderContainer.hide();
      itemsContainer.attr('location', sourceLocation).show();
    })
    .error( function() {
      loaderContainer.html('<p>Error connecting to Zotero server</p>');
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
  var initialCollectionsLoad = function () {
    var itemsContainer = $('#collections');
    var loaderContainer = $('#collections-loading');
    loadCollections(zoteroLibrary, itemsContainer, loaderContainer);
  }
  $('#load-collections-retry').live('click', function() {
    var itemsContainer = $('#collections');
    var loaderContainer = $('#collections-loading');
    initialCollectionsLoad(zoteroLibrary, itemsContainer, loaderContainer);
  });
  initialCollectionsLoad();
  
});
