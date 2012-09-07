$(document).ready(function(){

  var modal,
    $modal = $('.modal'),
    $documentwym,
    $loader;

  var zoteroForm = $('#zotero-information-edit');

  // Extend wysihtml5 composer with generateCitation command.
  // Can be executed with:
  //   {{editor instance}}.composer.commands.exec('generateCitation')
  wysihtml5.commands.generateCitation = {
    exec: function(composer, command, param) {
      var citation;

      citation = runCite(JSON.stringify(zoteroForm.data('asCslObject')));
      if (citation.search(/reference with no printed form/) > -1) {
        citation = '';
      }
      composer.setValue(citation);
    },

    state: function() {
      return false;
    },

    value: function() {
      return undefined;
    }
  }

  var editor = new wysihtml5.Editor('id_description', {
    toolbar: 'description-toolbar',
    parserRules: wysihtml5ParserRules,
    stylesheets: ['/static/function/wysihtml5/stylesheet.css']
  });

  editor.on('change:composer', function() {
    $('#autoupdate-citation')
      .attr('checked', false)
      .trigger('change');
  });

  $('#document-inline-edit')
    .on('change', '#autoupdate-citation', function() {
      zoteroForm.toggleClass('autoupdate-citation', this.checked);
    })
    .on('input change', '#zotero-information-edit.autoupdate-citation', function() {
      editor.composer.commands.exec('generateCitation');
    });

  $('#autoupdate-citation').trigger('click');

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
    var data = {
      'description': editor.getValue(),
      'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
    },
    zoteroFormData = zoteroForm.find(':input').serializeArray();

    $.each(zoteroFormData, function(k, v) {
      data[v.name] = v.value;
    });

    $.ajax({
      type: 'POST', url: '/admin/main/document/add/', data: data,
      success: function(data) {
        var doc = JSON.parse(data);
        $('#add-section input.ui-autocomplete-input').val(doc.document);
        $('#id_document').val(doc.id);
        $modal.modal('hide');
      }
    });
  });

});
