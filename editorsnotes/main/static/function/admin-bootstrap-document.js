$(document).ready(function() {

  var zoteroForm = $('#zotero-information-edit').trigger('input'),
    initialCitation = $('#id_description').val(),
    regexChars = /[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/gi,
    testcite,
    autoupdate;

  // If initial citation was blank or the same as a citation generated
  // from CSL, turn on autocomplete
  testcite = runCite(JSON.stringify(zoteroForm.data('asCslObject')));
  autoupdate = initialCitation === '' ||
               initialCitation.replace(regexChars, '')
                .search(testcite.replace(regexChars, '')) > -1;

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

  $('form')
    .on('change', '#autoupdate-citation', function() {
      zoteroForm.toggleClass('autoupdate-citation', this.checked);
    })
    .on('input change', '#zotero-information-edit.autoupdate-citation', function() {
      editor.composer.commands.exec('generateCitation');
    });

  if (autoupdate) {
    $('#autoupdate-citation').trigger('click');
  }

});
