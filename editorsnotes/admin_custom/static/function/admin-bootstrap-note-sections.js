$(document).ready(function () {

  $('#citation-items').sortable({
    placeholder: 'citation-placeholder',

    helper: function(event, item) {
      return $('<div>')
        .html($('.citation-document', item).text())
        .css({
          'height': '20px'
        });
    },
    cursor: 'pointer',
    cursorAt: {
      'left': 200,
      'top': 20
    },

    start: function(event, ui) {
      deactivateSections();
      $(this).addClass('sort-active');
      ui.item.hide();
      $('#citation-items').sortable('refreshPositions');
    },
    stop: function() {
      $(this).removeClass('sort-active');
    },
    update: function (event, ui) {
      ui.item.show();
      reorderSections();
    }

  });

  $('body')
    .on('click', '#add-citation', function (event) {
      event.preventDefault();
      deactivateSections();
      addSection();
    })
    .on('click', '.citation-edit:not(.citation-edit-active)', function (event) {
      event.preventDefault();
      deactivateSections();
      editSection($(this));
    })
    .on('click', '.add-new-document', function (event) {
      event.preventDefault();
      addDocumentModal($(this).siblings('input'));
    })
    .on('submit', '#main form', function () {
      deactivateSections();
      return true;
    })
    .on('click', '.save-document', function (event) {
      event.preventDefault();
      saveDocument($(this).closest('.modal'));
    })

});


/**
 * Removes current wysihtml5 instance and updates form values to reflect
 * any changes made to previous active section.
 *
 */
function deactivateSections() {
  $('.citation-edit-active').each(function () {
    var $activeSection = $(this)
      , toRemove
      , isBlankSection

    toRemove = [
      'iframe.wysihtml5-sandbox',
      'input[name="_wysihtml5_mode"]',
      '.btn-toolbar',
      '.edit-row'
    ]

    // Update text content that will be displayed with edited value in textarea
    $('.citation-notes', $activeSection)
      .html($activeSection.data('editor').getValue())
      .show();

    $activeSection
      .removeClass('citation-edit-active')
      .find(toRemove.join(', '))
        .remove();

    // Right now, a section is blank if it doesn't cite a document. This will
    // need to be updated when we have different kinds of sections
    isBlankSection = !$('.citation-document', $activeSection).text().trim().length;

    if (isBlankSection) {
      $activeSection.remove();
    }

  });

  // Update management form
  $('input[name="citation-TOTAL_FORMS"]').val($('.citation-edit').length);
  reorderSections();
}


/**
 * Returns representation of form as an object, for use in, e.g., ajax POST
 *
 */
function formToObject(form) {
  var formArray = $(':input', form).serializeArray()
    , formObject = {}

  for (var i = 0; i < formArray.length; i++) {
    formObject[formArray[i].name] = formArray[i].value;
  }

  return formObject;
}


/**
 * Changes ordering field for each visible citation based on postion in list.
 *
 */
function reorderSections() {
  var $sections = $('.citation-edit:visible');
  $sections.each(function () {
    $('input[name$="ordering"]', this)
      .val(Array.prototype.indexOf.call($sections, this) + 1)
  });
}


/**
 * Initialize a wysihtml5 instance for a given section
 *
 */
function editSection($section) {
  var editor
    , toolbar
    , textarea = $section.find('textarea[name$="notes"]')
    , $content = $section.find('.citation-notes');

  $section.addClass('citation-edit-active');

  textarea
    .attr('id', textarea.attr('name'))
    .css({
      'margin-bottom': '8px',
      'width': '99%',
      'height': (function (h) {
        return (h < 380 ? h : 380) + 120 + 'px'
      })($content.innerHeight())
    })
    .show();

  $content.hide();

  toolbar = $('#citation-toolbar').clone().show()
    .attr('id', $section.attr('id') + '-toolbar')
    .insertBefore(textarea);

  editor = new wysihtml5.Editor(textarea.attr('id'), {
    toolbar: toolbar.attr('id'),
    parserRules: wysihtml5ParserRules,
    stylesheets: ['/static/function/wysihtml5/stylesheet.css'],
    useLineBreaks: false
  });

  $section.data('editor', editor);

  $('<div class="row edit-row"><a class="btn pull-right">OK</a></div>')
    .appendTo($section)
    .on('click', function() {
      deactivateSections();
    });

}


/**
 * Add a new section with a blank input for the document field that allows
 * either selection of existing documents via autocomplete or the creation
 * of a new document (triggered by an anchor)
 *
 */
function addSection(after) {
  var $newSection = $('<div>')
    , $documentInput = $('<input type="text">')
    , lastSectionID
    , $newDocumentButton
    , autocompleteOptions = $('body').data('baseAutocompleteOptions');

  lastSectionID = Math.max.apply(Math, $('.citation-edit').map(function () {
    return (/\d+/).exec(this.id);
  }));

  $newSection
    .addClass('citation-edit citation')
    .prop('id', 'citation-' + (lastSectionID + 1))
    .append('<div class="citation-document"><i class="icon-file"></i></div>')
    .append('<div class="citation-notes"></div>')
    .prependTo('#citation-items');

  $('#citation-' + lastSectionID + ' .citation-fields')
    .clone()
    .appendTo($newSection)
    .children(':input').each(function () {
      this.name = this.name.replace(lastSectionID, lastSectionID + 1)
      switch (/\w+$/.exec(this.name)[0]) {
      case 'id':
        $(this).remove();
        break;
      case 'notes':
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
    .appendTo($newSection.find('.citation-document'))
    .addClass('document-autocomplete')
    .data('search-target', 'documents')
    .prop('placeholder', 'Type to search for a document, or add a new one by clicking the icon to the right.')
    .css({
      'margin': '0 4px',
      'width': '550px',
      'border-radius': '1px'
    })
    .autocomplete($.extend(autocompleteOptions, {
      'select': function (event, ui) {
        $this = $(event.target);

        $this.closest('.citation-document')
          .append(' ' + ui.item.value);
      
        $this.closest('.citation-edit')
          .find('input[name$="document"]')
            .val(ui.item.id);

        $this.remove();
        $newDocumentButton.remove();

      }
    }));

  $newDocumentButton = $('<a class="add-new-document" href="#_">')
    .html('<i class="icon-plus-sign"></i>')
    .insertAfter($documentInput);

  $newSection.trigger('click');
}


/**
 * Initialize a modal to add a document asynchronously
 *
 */
function addDocumentModal(sourceInput) {
  var $w = $(window)
    , $modal = $('.add-document-modal').clone()
    , textarea = $('textarea', $modal).prop('id', 'add-document-modal')
    , setModalHeight

  setModalHeight = function () {
    var bodyHeight = $modal.innerHeight() - 33
      - _.reduce($modal.children(':not(.modal-body)'), function (i, item) {
          return i + $(item).innerHeight()
        }, 0);

    $('.modal-body', $modal).css({
      'height': bodyHeight,
      'max-height': bodyHeight
    })
  }

  $modal
    .data('sourceInput', sourceInput)
    .on('hidden', function () {
      $modal.remove();
    })
    .css({
      'position': 'absolute',
      'width': $('#main').width() - 100,
      'height': (function () {
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
    success: function (data) {
      $('.zotero-information-edit', $modal)
        .html(data)
        .zotero({'description': '#' + textarea.prop('id')})
        .data('editor').on('load', function () {
          setModalHeight()
        });
    }
  });

}


function saveDocument($modal) {
  var zoteroContainer = $('.zotero-information-edit', $modal)
    , zoteroData = zoteroContainer.data('asZoteroObject')
    , description = zoteroContainer.data('editor').getValue()
    , data = {
      'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
      'description': description
    }

  if (!$.isEmptyObject(zoteroData)) {
    data.zotero_data = JSON.stringify(zoteroData);
  }

  if (!$('<div>').html(description).text().length) {
    alert('Enter a textual representation of this document before saving it.');
    return;
  }
    
  $.ajax({
    type: 'POST',
    url: '/admin/main/document/add/',
    data: data,
    success: function (newDocument) {
      var newDocumentObj = JSON.parse(newDocument)
        , oldInput = $modal.data('sourceInput');

      oldInput
        .siblings('.add-new-document').remove();
      
      oldInput
        .closest('.citation-edit').find('input[name$="document"]')
          .val(newDocumentObj.id);

      oldInput
        .replaceWith(' ' + newDocumentObj.value)

      $modal.modal('hide').remove();
    },
    error: function () {
    }
  });
}
