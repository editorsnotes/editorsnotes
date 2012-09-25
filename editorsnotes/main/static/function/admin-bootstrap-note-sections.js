$(document).ready(function() {
  var deactivateSections = function() {
    $('.note-section-active').each(function() {
      var $this = $(this),
        isBlankSection;
      $this
        .removeClass('note-section-active')
        .find('iframe.wysihtml5-sandbox, input[name="_wysihtml5_mode"], .btn-toolbar')
          .remove();
      $this.find('.note-section-content')
        .html($this.data('editor').getValue())
        .show();
      isBlankSection = !(
          $this.find('.document-autocomplete').length === 0 ||
          $this.find('.note-section-content').text().trim().length > 0)
      if (isBlankSection) {
        $this.remove();
      }
    });
  };

  var editSection = function($section) {
    var $content = $section.find('.note-section-content'),
      editor,
      textarea,
      toolbar;

    // Remove other editors & make this one active
    deactivateSections();
    $section.addClass('note-section-active');

    textarea = $section.find('textarea').length ? 
      $section.find('textarea').show() :
      $('<textarea>', {
        'id': $section.attr('id') + '-section',
        'value': $content.html(),
        'css': {
          'width': '99%',
          'height': $content.innerHeight() + 120 + 'px'
        }
      }).appendTo($section);

    $content.hide();

    toolbar = $('#note-section-toolbar').clone().show()
      .attr('id', $section.attr('id') + '-toolbar')
      .insertBefore(textarea);

    editor = new wysihtml5.Editor(textarea.attr('id'), {
      toolbar: toolbar.attr('id'),
      parserRules: wysihtml5ParserRules,
      stylesheets: ['/static/function/wysihtml5/stylesheet.css']
    });

    $section.data('editor', editor);
  };

  var addSection = function(after) {
    var $newSection,
      $documentInput,
      $addNewDocument,
      autocompleteOptions = $('body').data('baseAutocompleteOptions');

    $newSection = $('<div>')
      .addClass('note-section')
      .prop('id', 'note-section-new-' + ($('[id^="note-section-new"]').length + 1))
      .append('<div class="note-section-document"><i class="icon-file"></i></div>')
      .append('<div class="note-section-content"></div>')
      .prependTo('#sections')

    $documentInput = $('<input type="text">')
      .appendTo($newSection.find('.note-section-document'))
      .addClass('document-autocomplete')
      .data('search-target', 'documents')
      .prop('placeholder',
            'Type to search for a document, or add a new one by clicking the icon to the right.')
      .css({
        'margin': '0 4px',
        'width': '550px',
        'border-radius': '1px'
      })
      .autocomplete($.extend(autocompleteOptions, {
        'select': function(event, ui) {
          $(event.target).replaceWith(ui.item.value);
          $addNewDocument.remove();
        }
      }));

    $addNewDocument = $('<a id="add-new-document" href="#_">')
      .html('<i class="icon-plus-sign"></i>')
      .insertAfter($documentInput);
    
    $newSection.trigger('click');
  };

  $('#main')
    .on('click', '#add-note-section', function() {
      addSection();
    })
    .on('click', '.note-section:not(.note-section-active)', function() {
      editSection($(this));
    });
    
});
