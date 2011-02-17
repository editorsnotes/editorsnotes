$(document).ready(function () {

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

  // Initialize WYMeditors.
  $('textarea').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  }).wymeditor(wymconfig);

  // Initialize timeago.
  $('time.timeago').timeago();

  // Initialize autocomplete fields.
  var init_autocomplete = function() {
    $('<input type="text" class="vTextField"></input>')
    .insertBefore($(this))
    .autocomplete({
      source: function(request, response) {
        $.getJSON('/api/topics/', { q: request.term }, function(data) {
          response($.map(data, function(item, index) {
            return { label: item.preferred_name, id: item.id };
          }));
        });
      },
    minLength: 2,
      select: function(event, ui) {
        if (ui.item) {
          $(event.target).next().val(ui.item.id);
        }
      }
    });
    $(this).change(function(event) {
      console.log(event);
    });
  };

  $('.autocomplete-topics').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  })
  .each(init_autocomplete)
  .each(function() {
    if ($(this).val()) {
      var autocomplete = $(this).prev();
      $.getJSON('/api/topic/' + $(this).val() + '/', {}, function(data) {
        autocomplete.val(data.preferred_name);
      });
    }
  });

  // Initialize new inline rows when they are added.
  $('body').bind('inlineadded', function(e, row) {
    // Need to rewrap the row in non-Django jQuery, which has wymeditor loaded.
    $(row[0]).find('textarea').wymeditor(wymconfig);
    $(row[0]).find('.autocomplete-topics').each(init_autocomplete);
  });

  // Set autocomplete field after creating new related items.
  $('body').bind('addedviapopup', function(e, win, new_id, new_repr) {
    $('input#' + windowname_to_id(win.name))
    .prev('.ui-autocomplete-input')
    .val(html_unescape(new_repr));
  });

});
