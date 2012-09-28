$.fn.zotero = function (options) {
  var zoteroContainer = this
    , settings
    , toolbar
    , descriptionEdit
    , initArchiveAutocomplete

  settings = $.extend({
    'description': '#id_description'
  }, options);

  toolbar = ''
    + '<div id="description-toolbar" class="btn-toolbar" style="display: none;">'
    +   '<div class="btn-group">'
    +     '<a data-wysihtml5-command="bold" class="btn"><i class="icon-bold"></i></a>'
    +   '</div>'
    +   '<div class="btn-group">'
    +     '<a data-wysihtml5-command="italic" class="btn"><i class="icon-italic"></i></a>'
    +   '</div>'
    +   '<div class="pull-right">'
    +     '<a data-wysihtml5-command="generateCitation" class="btn">Generate citation</a>'
    +     '<span>Autoupdate? </span><input type="checkbox" class="autoupdate-toggle" />'
    +   '</div>'
    + '</div>'

  descriptionEdit = $(settings.description).before(toolbar);

  wysihtml5.commands.generateCitation = {
    exec: function (composer, command, param) {
      var CSL = zoteroContainer.data('asCslObject')
        , citation = EditorsNotes.CSL.makeCitation(CSL)
      if (citation.search(/reference with no printed form/) > -1) {
        citation = '';
      }
      composer.setValue(citation);
    },
    state: function () { return false; },
    value: function () { return undefined; }
  }

  initArchiveAutocomplete = function () {
    $('[data-zotero-key="archive"] textarea', zoteroContainer).autocomplete({
      source: function (request, response) {
        $.getJSON('/api/document/archives/', {'q': request.term}, function (data) {
          response($.map(data, function (item, index) {
            return { label: item.name };
          }));
        });
      }
    });
  }

  if (!EditorsNotes.CSL.hasOwnProperty('makeCitation')) {
    EditorsNotes.CSL.makeCitation = EditorsNotes.CSL.createCSLEngine('chicago_fullnote_bibliography2');
  }

  return this.each(function () {
    var editor = new wysihtml5.Editor(settings.description.slice(1), {
      toolbar: 'description-toolbar',
      parserRules: wysihtml5ParserRules,
      stylesheets: ['/static/function/wysihtml5/stylesheet.css']
    });

    editor
      .on('change:composer', function () {
        $('input.autoupdate-toggle').attr('checked', false).trigger('change');
      })
      .on('load', function () {
        if (editor.getValue() === '') {
          $('input.autoupdate-toggle').attr('checked', true).trigger('change');
        }
      });

    zoteroContainer.data('editor', editor);

    $('body')
      .on('change', 'input.autoupdate-toggle', 'change', function () {
        zoteroContainer.toggleClass('autoupdate-citation', this.checked);
      })

    initArchiveAutocomplete();

    zoteroContainer
      .on('input change', function () {
        var zoteroObject = EditorsNotes.zotero.zoteroFormToObject(zoteroContainer)
          , CSLObject = EditorsNotes.zotero.zoteroToCSL(zoteroObject)

        zoteroContainer
          .data('asZoteroObject', zoteroObject)
          .data('asCslObject', CSLObject)

        if (zoteroContainer.hasClass('autoupdate-citation')) {
          editor.composer.commands.exec('generateCitation');
        }

      })
      // Get template for form when item type selected
      .on('change', 'select[name="item-type-select"]', function () {
        var $itemTypeSelect = $(this)
          , itemType = $itemTypeSelect.val()

        if (!itemType.length) { return; }
        $.ajax({
          url: '/api/document/template/',
          data: {'itemType': itemType},
          success: function (data) {
            zoteroContainer
              .data('itemTypeSelect', $itemTypeSelect.parents('.control-group'))
              .html($(data).closest('#zotero-information-edit').html())
              .find('.zotero-entry-delete')
                .remove();
            initArchiveAutocomplete();
          }
        });
      })

      // Update creators' hidden inputs as they're changed
      .on('input change', '.zotero-creator', function () {
        var $this = $(this)
          , creatorObject = {};
        $this
          .find('.creator-attr').each(function () {
            creatorObject[$(this).data('creator-key')] = this.value;
          });
        $this
          .find('input:hidden')
          .val(JSON.stringify(creatorObject));
      })

      // Buttons for adding/removing creators
      .on('click', '.zotero-creator .add-creator', function () {
        var $oldCreator = $(this).parents('.zotero-creator'),
          $newCreator = $oldCreator.clone(true, true).insertAfter($oldCreator);
        $newCreator.find('textarea').val('').trigger('input');
      })
      .on('click', '.zotero-creator .remove-creator', function () {
        var $thisRow = $(this).parents('.zotero-creator');
        if ($thisRow.siblings('.zotero-creator').length) {
          $thisRow.remove();
        }
      })

  });
}
