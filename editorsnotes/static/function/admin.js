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
  $('textarea.xhtml-textarea').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  }).wymeditor(wymconfig);

  // Initialize timeago.
  $('time.timeago').timeago();

  // Initialize autocomplete fields.
  function init_autocomplete(collection, label_field, multiple) {
    return (function() {
      $('<input type="text" class="vTextField"></input>')
      .insertBefore($(this))
      .autocomplete({
        source: function(request, response) {
          $.getJSON('/api/' + collection + '/', { q: request.term }, 
                    function(data) {
                      response($.map(data, function(item, index) {
                        return { label: item[label_field], id: item.id };
                      }));
                    });
        },
        minLength: 2,
        focus: function() {
          return false;
        },
        select: function(event, ui) {
          if (ui.item) {
            var hidden = $(this).next();
            if (multiple) {
              var values = []
              if (hidden.val() !== '') {
                values = hidden.val().split(',');
              }
              values.push(ui.item.id);
              hidden.val(values.join(','));
              var choices = hidden.parent().find('ul.choices-display');
              var kill = $('<a class="remove-choice">Remove</a>');
              $('<li>' + ui.item.label + '</li>').appendTo(choices).prepend(kill);
              kill.bind('click', function(event) {
                values = hidden.val().split(',');
                for (var i = 0; i < values.length; i++) {
                  if (values[i] == ui.item.id) { break; }
                }
                values.splice(i, 1);
                hidden.val(values.join(','));
                $(this).parent().remove();
              });
              ui.item.value = '';
            } else {
              hidden.val(ui.item.id);
            }
          }
        }
      });
      if (multiple) {
        $(this).parent().append('<ul class="choices-display"></ul>')
      }
    });
  }

  function update_autocomplete(collection, label_field, multiple) {
    return (function() {
      var hidden = $(this);
      if (hidden.val()) {
        var autocomplete = hidden.prev();
        $.getJSON('/api/' + collection + '/' + hidden.val() + '/', {}, function(data) {
          if (! $.isArray(data)) {
            data = [ data ];
          }
          if (multiple) {
            var choices = hidden.parent().find('ul.choices-display');
            $.each(data, function() {
              var item = this;
              var kill = $('<a class="remove-choice">Remove</a>');
              $('<li>' + item[label_field] + '</li>').appendTo(choices).prepend(kill);
              kill.bind('click', function(event) {
                var values = hidden.val().split(',');
                for (var i = 0; i < values.length; i++) {
                  if (values[i] == item.id) { break; }
                }
                values.splice(i, 1);
                hidden.val(values.join(','));
                $(this).parent().remove();
              });
            });
          } else {
            autocomplete.val(data[0][label_field]);
          }
        });
      }
    });
  }

  var init_autocomplete_topics = init_autocomplete('topics', 'preferred_name');
  var update_autocomplete_topics = update_autocomplete('topics', 'preferred_name');

  var init_autocomplete_multiple_topics = init_autocomplete('topics', 'preferred_name', true);
  var update_autocomplete_multiple_topics = update_autocomplete('topics', 'preferred_name', true);

  var init_autocomplete_documents = init_autocomplete('documents', 'description');
  var update_autocomplete_documents = update_autocomplete('documents', 'description');

  var init_autocomplete_transcripts = init_autocomplete('transcripts', 'description');
  var update_autocomplete_transcripts = update_autocomplete('transcripts', 'description');

  $('.autocomplete-topics').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  })
  .each(init_autocomplete_topics)
  .each(update_autocomplete_topics);

  $('.autocomplete-multiple-topics').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  })
  .each(init_autocomplete_multiple_topics)
  .each(update_autocomplete_multiple_topics);

  $('.autocomplete-documents').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  })
  .each(init_autocomplete_documents)
  .each(update_autocomplete_documents);

  $('.autocomplete-transcripts').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  })
  .each(init_autocomplete_transcripts)
  .each(update_autocomplete_transcripts);

  // Initialize new inline rows when they are added.
  $('body').bind('inlineadded', function(e, row) {
    // Need to rewrap the row in non-Django jQuery, which has wymeditor loaded.
    $(row[0]).find('textarea.xhtml-textarea').wymeditor(wymconfig);
    $(row[0]).find('.autocomplete-topics').each(init_autocomplete_topics);
    $(row[0]).find('.autocomplete-documents').each(init_autocomplete_documents);
    $(row[0]).find('.autocomplete-transcripts').each(init_autocomplete_transcripts);
  });

  // Set autocomplete field after creating new related items.
  $('body').bind('addedviapopup', function(e, win, new_id, new_repr) {
    var hidden = $('input#' + windowname_to_id(win.name));
    if (hidden.hasClass('vManyToManyRawIdAdminField')) {
      var choices = hidden.parent().find('ul.choices-display');
      var kill = $('<a class="remove-choice">Remove</a>');
      $('<li>' + new_repr + '</li>').appendTo(choices).prepend(kill);
      kill.bind('click', function(event) {
        values = hidden.val().split(',');
        for (var i = 0; i < values.length; i++) {
          if (values[i] == new_id) { break; }
        }
        values.splice(i, 1);
        hidden.val(values.join(','));
        $(this).parent().remove();
      });
    } else {
      hidden.prev('.ui-autocomplete-input')
      .val(html_unescape(new_repr));
    }
  });

});
