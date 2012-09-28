$(document).ready(function() {
  var deactivateSections
    , editSection
    , addSection
    , addDocument

  deactivateSections = function() {
    $('.note-section-active').each(function() {
      var $this = $(this)
        , isBlankSection;

      $this
        .removeClass('note-section-active')
        .find('iframe.wysihtml5-sandbox, input[name="_wysihtml5_mode"], .btn-toolbar')
          .remove();

      $this.find('.note-section-content')
        .html($this.data('editor').getValue())
        .show();

      isBlankSection = !(
          $this.find('.document-autocomplete').length === 0 ||
          $this.find('.note-section-content').text().trim().length > 0);

      if (isBlankSection) {
        $this.remove();
      }
    });
  };

  editSection = function($section) {
    var editor
      , textarea
      , toolbar
      , $content = $section.find('.note-section-content');

    deactivateSections();
    $section.addClass('note-section-active');

    textarea = $section.find('textarea').length ? 
      $section.find('textarea').show() :
      $('<textarea>', {
        'id': $section.attr('id') + '-section',
        'value': $content.html(),
        'css': {'width': '97%'}
      }).appendTo($section);

    textarea.css('height',
      (function(h) {
        return (h < 380 ? h : 380) + 120 + 'px'
      })($content.innerHeight())
    );

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

  addSection = function(after) {
    var $newSection
      , $documentInput
      , $addNewDocument
      , autocompleteOptions = $('body').data('baseAutocompleteOptions');

    $newSection = $('<div>')
      .addClass('note-section')
      .prop('id', 'note-section-new-' + ($('[id^="note-section-new"]').length + 1))
      .append('<div class="note-section-document"><i class="icon-file"></i></div>')
      .append('<div class="note-section-content"></div>')
      .prependTo('#sections');

    $documentInput = $('<input type="text">')
      .appendTo($newSection.find('.note-section-document'))
      .addClass('document-autocomplete')
      .data('search-target', 'documents')
      .prop('placeholder', 'Type to search for a document, or add a new one by clicking the icon to the right.')
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

    $addNewDocument = $('<a class="add-new-document" href="#_">')
      .html('<i class="icon-plus-sign"></i>')
      .insertAfter($documentInput);
    
    $newSection.trigger('click');
  };

  addDocument = function(source) {
    var $w = $(window)
      , modal 
      , $modal
      , setBodyHeight

    modal= ''
      + '<div class="modal add-document-modal hide form-horizontal row span10">'
      +   '<div class="modal-header">'
      +     '<button type="button" data-dismiss="modal" class="close" aria-hidden="true">&times;</button>'
      +     '<h3>Add document</h3>'
      +   '</div>'
      +   '<div class="document-description modal-header">'
      +     '<textarea id="description" style="width: 98%"></textarea>'
      +   '</div>'
      +   '<div class="modal-body">'
      +     '<div class="zotero-information-edit">Loading... </div>'
      +   '</div>'
      +   '<div class="modal-footer">'
      +     '<a href="#_" class="btn" data-dismiss="modal">Cancel</a>'
      +     '<a href="#_" class="btn btn-primary save-document">Save</a>'
      +   '</div>'
      + '</div>';

    setBodyHeight = function() {
      var bodyHeight = $modal.innerHeight()
        - $('.modal-header:not(.document-description)', $modal).innerHeight()
        - $('.document-description', $modal).innerHeight()
        - $('.modal-footer', $modal).innerHeight()
        - 33
      $('.modal-body', $modal).css({
        'height': bodyHeight,
        'max-height': bodyHeight
      })
    }

    $modal = $(modal)
      .css({
        'position': 'absolute',
        'width': $('#main').width() - 100,
        'height': (function() {
          var h = $w.height() - 40;
          return h > 500 ? h : 500;
        })()
      })
      .appendTo('body')
      .modal()
      // Don't ask me why, but we need to do this twice for webkit
      .position({
        'my': 'top',
        'at': 'top',
        'of': $w,
        'collision': 'none',
        'offset': '0 20'
      })
      .position({
        'my': 'top',
        'at': 'top',
        'of': $w,
        'collision': 'none',
        'offset': '0 20'
      })

    setBodyHeight();

    $.ajax({
      url: '/api/document/template/',
      success: function(data) {
        $('.zotero-information-edit', $modal)
          .html(data)
          .zotero({'description': '#description'})
          .data('editor').on('load', function() { setBodyHeight() })
      }
    });

    $modal
      .on('click', '.save-document', function() {
        var zoteroContainer = $('.zotero-information-edit');
        $.ajax({
          type: 'POST',
          url: '/admin/main/document/add/',
          data: {
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
            'zotero_data': JSON.stringify( zoteroContainer.data('asZoteroObject') ),
            'description': zoteroContainer.data('editor').getValue()
          },
          success: function(data) {
            var newDocument = JSON.parse(data)
              , oldInput = $(source)

            oldInput.siblings('a').remove();
            oldInput.replaceWith(newDocument.description);
            $modal.modal('hide').remove();
          },
          error: function(data) {
          }
        });
      })
      .on('hidden', function() {
        $modal.remove();
      })
  }



  /***********************************************
   * Bindings
   **********************************************/
  $('body')
    .on('click', '#add-note-section', function() {
      addSection();
    })
    .on('click', '.note-section:not(.note-section-active)', function() {
      editSection($(this));
    })
    .on('click', '.add-new-document', function() {
      addDocument($(this).siblings('input'));
    })
    
});
