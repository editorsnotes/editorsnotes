$(document).ready(function(){
  var csrf_token = $("input[name='csrfmiddlewaretoken']").attr('value');
  var collectionCounter = 1;
  
  $('.library-item').live('click', function(){
    var selectedLibrary = $(this);
    var collectionsContainer = $('#collections');
    var collectionsLoaderContainer = $('#collections-loading');
    var firstCollectionItem = $('<li>')
        .attr({'id' : 'collection-0',
               'class' : 'collection-item',
               'location' : selectedLibrary.attr('location')})
        .html('<h3>' + selectedLibrary.text() + '</h3>');
    $('#libraries-container').hide();
    collectionsContainer.append(firstCollectionItem);
    loadCollections(selectedLibrary.attr('location'), 1, collectionsContainer, collectionsLoaderContainer);
  });
  
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
  
  $('.collection-children-toggle').live('click', function(){
    var topCollection = $(this).next('.collection-item');
    if (topCollection.hasClass('collection-collapsed')) {
      $(this).attr('src', '/media/style/icons/collapse.png');
      var loadingContainer = $('<div>')
      var collectionChildrenContainer = $('<ul>')
        .attr({'id' : topCollection.attr('id') + '-children', 'class' : 'collection-child'});
      collectionChildrenContainer.append(loadingContainer).insertAfter(topCollection);
      loadCollections(topCollection.attr('location'), 0, collectionChildrenContainer, loadingContainer);
      topCollection.toggleClass('collection-collapsed');
    }
    else {
      $(this).attr('src', '/media/style/icons/expand.png');
      topCollection.next('ul').remove()
      topCollection.toggleClass('collection-collapsed');
    }
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
      var newContainer = $('<div class="zotero-item-selected">').append(data).append(itemData['citation']);
      newContainer.append(data);
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
    var selectedItems = $('#items-to-post .zotero-item-selected input')
    var itemsArray = new Array
    $.each(selectedItems, function(key, item) {
      var itemData = JSON.parse($(item).attr('value'));
      itemData.related_topic = relatedTopic;
      itemData.related_note = relatedNote;
      itemsArray.push(JSON.stringify(itemData));
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
  var loadLibraries = function (libraryContainer, loaderContainer) {
    loaderContainer.html('Connecting to Zotero... <img class="loader" src="/media/style/icons/ajax-loader.gif">').show();
    $.getJSON('libraries/', function(data) {
      var i = 1
      $.each(data.libraries, function (key, value) {
        var library = $('<li>')
          .attr({
            'class' : 'library-item',
            'location' : value.location,
            'id' : 'library-' + i
          })
          .text(value.title);
        libraryContainer.append(library);
        i++
      });
      loaderContainer.hide();
      libraryContainer.show();
    })
    .error(function() {
      loaderContainer.html('<p>Error reaching Zotero server.<p><a href="#" class="button" id="load-libraries-retry">Retry</a>').show();
    });
  };

  var loadCollections = function (libraryURL, topLevel, collectionContainer, loaderContainer) {
    loaderContainer.html('Loading collections... <img class="loader" src="/media/style/icons/ajax-loader.gif">').show();
    $.getJSON('collections/', {'loc' : libraryURL, 'top' : topLevel }, function(data) {
      $.each(data.collections, function (key, value) {
        var collection = $('<li>')
          .attr({
            'class' : 'collection-item',
            'location' : value.location,
            'id' : 'collection-' + collectionCounter
          })
          .html(value.title);
        if (value.has_children) {
          collection.addClass('collection-has-children collection-collapsed');
          var collectionOffset = collection.offset();
          var toggler = $('<img src="/media/style/icons/expand.png">')
            .attr({'class' : 'collection-children-toggle collection-collapsed'});
          if (!topLevel){toggler.addClass('collection-child');}
        }
        if (typeof(toggler)!='undefined'){collectionContainer.append(toggler);}
        collectionContainer.append(collection);
        collectionCounter++
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
    loadCollections(zoteroLibrary, 1, itemsContainer, loaderContainer);
  }
  $('#load-collections-retry').live('click', function() {
    var itemsContainer = $('#collections');
    var loaderContainer = $('#collections-loading');
    initialCollectionsLoad(zoteroLibrary, itemsContainer, loaderContainer);
  });
  
  //Get libraries on page load
  var initialLibrariesLoad = function () {
    var contentContainer = $('#libraries');
    var loaderContainer = $('#libraries-loading');
    loadLibraries(contentContainer, loaderContainer);
  }
  $('#load-libraries-retry').live('click', function() {
    initialLibrariesLoad();
  });
  
  initialLibrariesLoad();
});
