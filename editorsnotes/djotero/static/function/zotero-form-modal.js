$(document).ready(function(){

  var modal,
    $modal = $('.modal'),
    $documentwym,
    $loader;

  $('#add-document-modal').live('click', function(){

    if ($modal.hasClass('modal-initialized')) {
      $modal.modal('show');
    } else {
      $modal
        .modal({backdrop: 'static'})
        .css({
          'width': '800px',
          'top': '45%',
          'margin-left': function() {
            return -($(this).width() / 2);
          }
        }).addClass('modal-initialized');
      $loader = $modal.find('#modal-loading')
        .position({'of' : '#modal-edit-row'})
        .hide();

      $.ajax({
        url: '/api/document/template/',
        success: function(data) {
          $modal.find('.zotero-information-edit')
            .append($(data).closest('.zotero-information-edit').html());
        }
      });
    }

  });

  $('#document-edit-close').live('click', function(){
    var $zoteroContainer = $('.zotero-information-edit');
    $modal.modal('hide');
    $zoteroContainer
      .html($zoteroContainer.data('itemTypeSelect'))
      .find('option').first().prop('selected', true).blur();
  });

  $('#document-save').live('click', function() {
    var zoteroForm = $('#document-zotero-information table');

    $.ajax({
      type: 'POST',
      url: '/document/add/',
      data: {
        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
        'zotero-string': JSON.stringify( zoteroFormToObject(zoteroForm, true) ),
        'document-description': $documentwym.html()
      },
      success: function(data) {
        var doc = JSON.parse(data);
        $('#add-section input.ui-autocomplete-input').val(doc.document);
        $('#id_document').val(doc.id);
        $modal.modal('hide');
      }
    });
  });

});
