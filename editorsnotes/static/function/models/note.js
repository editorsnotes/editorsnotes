$(document).ready(function() {

  var url = $.param.fragment();
  if ( url == '' ) {
    window.location.replace(window.location.href + '#note');
    url = $.param.fragment();
  }

  var tabs = $('#tabs a');

  tabs.click(function(e) {
    e.preventDefault();
    var index = $(this).attr('href').match(/#(.+)-tab/)[1];
    $.bbq.pushState(index, 2);
  });

  $(window).bind('hashchange', function(e) {
    var index = $.bbq.getState();
    $.each(index, function(key, value) {
      var tabToOpen = tabs.filter('a[href*="' + key + '"]');
      if (tabToOpen.length > 0) {
        tabToOpen.tab('show');
      }
    });
  }).trigger('hashchange');

  var $documentField = $('.autocomplete-documents');
  var $autocomplete = $('<input type="text">')
    .prependTo($documentField.parent())
    .autocomplete({
      source: function(request, response) {
        $.getJSON('/api/documents/', { q: request. term}, function(data) {
          response($.map(data, function(item, index) {
            return { label: item.description, id: item.id };
          }));
        });
      },
      minLength: 2,
      select: function(event, ui) { $documentField.val(ui.item.id) }
    });

    $('<label>Document</label>').insertBefore($autocomplete);
    $('<a href="#_" id="add-document-modal"><i class="icon-plus-sign"></i></a>')
      .insertAfter($autocomplete);

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
  $('textarea[name="content"]').wymeditor(wymconfig);

  $('#sort-by-date').click(function(event) {
    event.preventDefault();
    var $sortAnchor = $(this);
    if ($sortAnchor.hasClass('active')) {
      $sortAnchor
        .toggleClass('ascending descending')
        .find('i')
          .toggleClass('icon-chevron-up icon-chevron-down');
    } else {
      $sortAnchor
        .toggleClass('inactive active')
        .siblings('a')
          .removeClass('active')
          .addClass('inactive');
    }
    $docs = $('#note-sections').children();
    $sortedDocs = _.sortBy($docs, function(doc) {
      var $doc = $(doc),
        date;
      
      date = '' + ($doc.find('.document').data('edtf-date') || '99999999');
      if (date.indexOf('/') > 0) {
        date = date.slice(0, date.indexOf('/'))
      }
      date.replace(/[^0-9]/, '');
      while (date.length < 8) {
        date += '0'
      };

      return date
    });
    if ($sortAnchor.hasClass('descending')) {
      $sortedDocs = $.makeArray($sortedDocs).reverse()
    }
    $('#note-sections').append($sortedDocs);
  });


});
