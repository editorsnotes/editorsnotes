$(document).ready(function(){
  // Selection for lists
  $(".djotero-list.active li").live({
    mouseenter : function() {
      if ( $(this).hasClass('item-selected') == false ) {
        $(this).addClass('item-hover');
      }
    },
    mouseleave : function() {
      $(this).removeClass('item-hover');
    },
    click : function() {
      $(this).siblings().removeClass('item-selected');
      $(this).addClass('item-selected');
    }
  });

  $('.library-item').live('click', function() {
    $('.after-library').show();
  });

  //
  // Ajax functions
  //
  var csrf_token = $("input[name='csrfmiddlewaretoken']").attr('value');
  
  // 1. Show accessible Zotero libraries
  $('#get-libraries').click(function(){
    $(this).replaceWith('<img src="/media/style/icons/ajax-loader.gif">');
    $.getJSON('libraries/', function(data) {
      $('#libraries img').remove();
      var i = 1
      $.each(data.libraries, function (key, value) {
        var library = $('<li>')
          .attr({
            'class' : 'library-item',
            'location' : value.location,
            'id' : 'library-' + i
          })
          .text(value.title);
        $('#library-list').append(library);
        i++
      });
    });
  });

  // 2. Show list of collections within a library
  $('#get-collections').click(function(){
    $(this).replaceWith('<img src="/media/style/icons/ajax-loader.gif">');
    $('#library-list').removeClass('active');
    var base = $("#library-list .item-selected").attr('location');
    $.getJSON('collections/', {'loc' : base }, function(data) {
      $('#collections img').remove();
      var i = 1
      $.each(data.collections, function (key, value) {
        var collection = $('<li>')
          .attr({
            'class' : 'collection-item',
            'location' : value.location,
            'id' : 'collection-' + i
          })
          .text(value.title);
        $('#collection-list').append(collection);
        i++
      });
    });
  });

  // 3. List items within library or collection
  $("#get-items").click(function(){
    $(this).replaceWith('<img src="/media/style/icons/ajax-loader.gif">');
    // Determine source
    if( $('#collection-list').find('.item-selected').length > 0 ) {
      var selectedSource = $("#collection-list .item-selected").attr('location');
    }
    else {
      var selectedSource = $("#library-list .item-selected").attr('location');
    }
    // Set options
    var queryOptions = new Object
    $('.items-option').each(function() {
      var optVal = $(this).val()
      var optKey = $(this).parent().attr('key')
      if ( optVal != '' ) {
        queryOptions[optKey] = optVal
      }
    });
    $.getJSON('items/', {'loc' : selectedSource, 'opts' : JSON.stringify(queryOptions) }, function(data) {
      $('#access').hide();
      $('#items').show();
      var i = 1
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
    });
  });
  
  // 4. Post selected items
  $('#post-items').click(function(){
    $(this).replaceWith('<img src="/media/style/icons/ajax-loader.gif">');
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
});
