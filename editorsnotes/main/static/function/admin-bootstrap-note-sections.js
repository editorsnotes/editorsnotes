$(document).ready(function() {
  var deactivateSections
    , formToObject
    , updateManagementForm
    , editSection
    , addSection
    , addDocument

  /**
   * Removes current wysihtml5 instance and updates form values to reflect
   * any changes made to previous active section.
   *
   */
  deactivateSections = function() {
    $('.note-section-active').each(function() {
      var $this = $(this)
        , wysihtml5Sections
        , isBlankSection

      // Update text content that will be displayed with edited value in textarea
      $('.note-section-content', $this)
        .html($this.data('editor').getValue())
        .show();

      wysihtml5Selectors = [
        'iframe.wysihtml5-sandbox',
        'input[name="_wysihtml5_mode"]',
        '.btn-toolbar'
      ]

      $this.removeClass('note-section-active')
        .find(wysihtml5Selectors.join(', '))
          .remove();

      // Right now, a section is blank if it doesn't cite a document. This will
      // need to be updated when we have different kinds of sections
      isBlankSection = !(
        $this.find('.document-autocomplete').length === 0
      );

      if (isBlankSection) $this.remove();

      // Update the management after everything else has been done
      $('input[name="sections-TOTAL_FORMS"]').val($('.note-section').length)

    });
  };

  /**
   * Returns representation of form as an object, for use in, e.g., ajax POST
   *
   */
  formToObject = function(form) {
    var formArray = $(':input', form).serializeArray()
      , formObject = {}

    for (var i = 0; i < formArray.length; i++) {
      formObject[formArray[i].name] = formArray[i].value;
    }

    return formObject;
  }
  
  
  /**
   * Initialize a wysihtml5 instance for a given section
   *
   */
  editSection = function($section) {
    var editor
      , toolbar
      , textarea = $section.find('textarea[name$="content"]')
      , $content = $section.find('.note-section-content');

    $section.addClass('note-section-active');

    textarea
      .attr('id', textarea.attr('name'))
      .css({
        'width': '97%',
        'height': (function(h) {
          return (h < 380 ? h : 380) + 120 + 'px'
        })($content.innerHeight())
      })
      .show();

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


  /**
   * Add a new section with a blank input for the document field that allows
   * either selection of existing documents via autocomplete or the creation
   * of a new document (triggered by an anchor)
   *
   */
  addSection = function(after) {
    var $newSection = $('<div>')
      , $documentInput = $('<input type="text">')
      , lastSectionID
      , $newDocumentButton
      , autocompleteOptions = $('body').data('baseAutocompleteOptions');

    lastSectionID = Math.max.apply(Math, $('.note-section').map(function() {
      return /\d/.exec(this.id);
    }))

    $newSection
      .addClass('note-section')
      .prop('id', 'note-sections-' + (lastSectionID + 1))
      .append('<div class="note-section-document"><i class="icon-file"></i></div>')
      .append('<div class="note-section-content"></div>')
      .prependTo('#sections');

    $('#note-sections-' + lastSectionID + ' .note-section-fields')
      .clone()
      .appendTo($newSection)
      .children('input, textarea').each(function() {
        this.name = this.name.replace(lastSectionID, lastSectionID + 1)
        switch (/\w+$/.exec(this.name)[0]) {
        case 'id':
          $(this).remove();
          break;
        case 'content':
          $(this).val('').html('').css('height', '1px');
          break;
        case 'note':
          break;
        case 'DELETE':
          $(this).val('').prop('checked', false);
          break;
        default:
          $(this).val('');
          break;
        }
      });

    $documentInput 
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
          $('input[name$="document"]', $newSection).val(ui.item.id);
          $newDocumentButton.remove();
        }
      }));

    $newDocumentButton = $('<a class="add-new-document" href="#_">')
      .html('<i class="icon-plus-sign"></i>')
      .insertAfter($documentInput);

    $newSection.trigger('click');
  };

  /**
   * Initialize a modal to add a document asynchronously
   *
   */
  addDocument = function(source) {
    var $w = $(window)
      , $modal = $('.add-document-modal').clone()
      , textarea = $('textarea', $modal).prop('id', 'add-document-modal')
      , setModalHeight

    setModalHeight = function() {
      var bodyHeight = $modal.innerHeight() - 33
        - _.reduce($modal.children(':not(.modal-body)'), function(i, item) {
            return i + $(item).innerHeight()
          }, 0);

      $('.modal-body', $modal).css({
        'height': bodyHeight,
        'max-height': bodyHeight
      })
    }

    $modal
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

    setModalHeight();

    $.ajax({
      url: '/api/document/template/',
      success: function(data) {
        $('.zotero-information-edit', $modal)
          .html(data)
          .zotero({'description': '#' + textarea.prop('id')})
          .data('editor').on('load', function() {
            setModalHeight()
          });
      }
    });

    $modal
      .on('click', '.save-document', function(event) {
        event.preventDefault();
        var zoteroContainer = $('.zotero-information-edit', $modal);
        $.ajax({
          type: 'POST',
          url: '/admin/main/document/add/',
          data: {
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
            'zotero_data': JSON.stringify(zoteroContainer.data('asZoteroObject')),
            'description': zoteroContainer.data('editor').getValue()
          },
          success: function(data) {
            var newDocument = JSON.parse(data)
              , oldInput = $(source)

            oldInput
              .siblings('.add-new-document').remove();
            
            oldInput
              .closest('.note-section').find('input[name$="document"]')
                .val(newDocument.id);

            oldInput
              .siblings('.add-new-document').remove();

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
    /*
    .on('click', function() {
      deactivateSections();
    })
    .on('click', '#main, .modal, .modal-backdrop', function(e) {
      e.stopPropagation();
    })
    */
    .on('click', '#add-note-section', function(event) {
      event.preventDefault();
      deactivateSections();
      addSection();
    })
    .on('click', '.note-section:not(.note-section-active)', function(event) {
      event.preventDefault();
      deactivateSections();
      editSection($(this));
    })
    .on('click', '.add-new-document', function(event) {
      event.preventDefault();
      addDocument($(this).siblings('input'));
    })
    .on('submit', '#main form', function(event) {
      deactivateSections();
      return false;
    })
    
});
