$(document).ready(function () {

  // Base WYMeditor configuration.
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

  var footnote_editors = {
    done: false,
    width: 800,
    setup: function() {
      if (footnote_editors.done) { return; }
      footnote_editors.done = true;
      $('input[type=checkbox]').filter(function() {
        return this.id.match(/id_footnotes-\d+-EDIT/);
      }).click(footnote_editors.on_edit_checkbox);
    },
    resize: function(event, ui) {
      var title = $(event.target).prev().find('.ui-dialog-title');
      title.ellipsis(Math.min(ui.size.width, footnote_editors.width) - 50);
    },
    parse_wym_index: function(wym_box) {
      var classes = wym_box.attr('class').split(' ');
      for (var i = 0; i < classes.length; i++) {
        var match = classes[i].match(/^wym_box_(\d+)$/);
        if (match) {
          return parseInt(match[1]);
        }
      }
      return -1;
    },
    close: function(event, ui) {
      var wym_box = $(event.target).find('.wym_box');
      var textarea = wym_box.prev();
      var row = $('#' + textarea.attr('name').split('-').splice(0,2).join('-'));
      var display = row.find('.content .readonly');
      if (display.text().replace(/^\s+|\s+$/g, '').length == 0) {
        django.jQuery('#' + row.attr('id') + ' a.inline-deletelink').click();
      }
      delete WYMeditor.INSTANCES[footnote_editors.parse_wym_index(wym_box)];
      $('#transcript_form').append(textarea);
      wym_box.remove();
    },
    get_wymeditor_for: function(textarea) {
      var wym_index = footnote_editors.parse_wym_index(textarea.next());
      if (wym_index >= 0) {
        return $.wymeditors(wym_index);
      } else {
        return null;
      }
    },
    show_editor_for_row: function(row) {
      var textarea = $('#id_' + row.attr('id') + '-content');
      var editor_id = 'id_' + row.attr('id') + '-editor';
      var editor = $('#' + editor_id);
      if (editor.length == 0) {
        editor = $(document.createElement('div'));
        editor.attr('id', editor_id);
        $(document.body).append(editor);
        editor.dialog({ 
          autoOpen: false, 
          modal: true,
          draggable: true,
          resizable: true,
          close: footnote_editors.close,
          width: footnote_editors.width,
          title: row.find('.inline_label').text(),
          buttons: {
            'OK': function() { 
              var textarea = $(this).find('.hidden-textarea');
              var wym = footnote_editors.get_wymeditor_for(textarea);
              wym.update();
              var row = $('#' + textarea.attr('name').split('-').splice(0,2).join('-'));
              var display = row.find('.content .readonly');
              display.html(textarea.val());
              if (display.text().replace(/^\s+|\s+$/g, '').length == 0) {
                wym.status('Footnotes cannot be empty.');
              } else {
                $(this).dialog('close'); 
                row.find('#id_' + row.attr('id') + '-EDIT').attr(
                  'checked', 'checked');
              }
            },
            'Cancel': function() { 
              $(this).dialog('close'); 
            }
          }
        });
        editor.bind('dialogresize', footnote_editors.resize);
        editor.dialog('widget').find('.ui-dialog-content').css('padding', '1em');
        //editor.dialog('option', 'position', {
        //  my: 'top', at: 'bottom', of: link, offset: '0 5', collision: 'none', 
        //  using: footnote_editors.using });
      }
      editor.append(textarea);
      textarea.wymeditor(wymconfig);
      editor.dialog('open');
    },
    on_edit_checkbox: function(event) {
      event.preventDefault();
      footnote_editors.show_editor_for_row(
        $(event.target).parents('.dynamic-footnotes'));
    }
  };

  var transcript_editor = {
    stamps: [],
    wymconfig: $.extend(true, {}, wymconfig),
    setup: function() {
      transcript_editor.wymconfig.postInit = function(wym) {
        // Add footnote button to transcript editor.
        var button = ''
          + '<li class="wym_tools_footnote">'
          + '<a name="Footnote" title="Footnote" href="#"'
          + ' style="background-image:'
          + ' url(/static/function/wymeditor/skins/custom/footprint.png)">'
          + 'Footnote'
          + '</a></li>';
        $(wym._box).find(wym._options.toolsSelector + 
                         wym._options.toolsListSelector).append(button);
        // Handle footnote button click.
        $(wym._box).find('li.wym_tools_footnote a').click(function() {
          var selection = wym._iframe.contentWindow.getSelection();
          var selected_text = selection.toString();
          var overlap = false;
          // Check to make sure we're not already inside footnoted text.
          $(wym._doc.body).find('a.footnote').each(function(index) {
            if (selection.containsNode(this, true)) {
              overlap = true;
              return false;
            }
          });
          if (overlap) {
            wym.status('Footnotes cannot overlap.');
          } else if (selected_text) {
            // Create a footnote link with a temporary stamp.
            wym.status('&nbsp;');
            var stamp = wym.uniqueStamp();
            transcript_editor.stamps.push(stamp);
            wym._exec(WYMeditor.CREATE_LINK, stamp);
            $(wym._doc.body).find(
              'a[href=' + stamp + ']').attr(WYMeditor.CLASS, 'footnote')
            // Notify the default admin routines that we've added a footnote.
            django.jQuery('#footnotes-group .add-row a').click();
          } else {
            wym.status('You must select some text to add a footnote.');
          }
        });
        // Hide the default admin button for adding footnotes.
        $('#footnotes-group .add-row a').hide();

        $('body').bind('footnoterowadded', function(e, row) {
          row.find('.controls').addClass('new-controls');
          var stamp = transcript_editor.stamps.shift();
          row.find('#id_' + row.attr('id') + '-stamp').attr('value', stamp);
          var title = $(wym._doc.body).find('a[href="' + stamp + '"]').text();
          row.find('.inline_label').text(title);
          row.find('input[type=checkbox]').filter(function() {
            return this.id.match(/id_footnotes-\d+-EDIT/);
          }).click(footnote_editors.on_edit_checkbox);
          footnote_editors.show_editor_for_row(row);
        });

        $('body').bind('footnoterowremoved', function(e, row) {
          var row_id = row.attr('id');
          var stamp = row.find('#id_' + row_id + '-stamp').attr('value');
          var selection = wym._iframe.contentWindow.getSelection();
          selection.selectAllChildren(
            $(wym._doc.body).find('a[href="' + stamp + '"]')[0]);
          wym._exec(WYMeditor.UNLINK)
          wym._iframe.contentWindow.focus();
          selection.collapseToStart();
        });
      };

      $('textarea#id_content').wymeditor(transcript_editor.wymconfig);
    }
  };

  // Setup footnote editors.   
  footnote_editors.setup();

  // Initialize content WYMeditor.
  transcript_editor.setup();

  // Initialize timeago.
  $('time.timeago').timeago();

  // Initialize autocomplete fields.
  var init_autocomplete_documents = function() {
    $('<input type="text" class="vTextField"></input>')
    .insertBefore($(this))
    .autocomplete({
      source: function(request, response) {
        $.getJSON('/api/documents/', { q: request.term }, function(data) {
          response($.map(data, function(item, index) {
            return { label: item.description, id: item.id };
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

  $('.autocomplete-documents').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  })
  .each(init_autocomplete_documents)
  .each(function() {
    if ($(this).val()) {
      var autocomplete = $(this).prev();
      $.getJSON('/api/documents/' + $(this).val() + '/', {}, function(data) {
        autocomplete.val(data.description);
      });
    }
  });

  // Set autocomplete field after creating new related items.
  $('body').bind('addedviapopup', function(e, win, new_id, new_repr) {
    $('input#' + windowname_to_id(win.name))
    .prev('.ui-autocomplete-input')
    .val(html_unescape(new_repr));
  });

});
