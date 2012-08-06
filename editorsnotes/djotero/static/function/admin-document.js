$(document).ready(function() {
  $('.xhtml-textarea').wymeditor(zoteroWymSettings);

  $('.zotero-creator').live('input', function() {
    var $this = $(this),
      $creatorAttrs = $this.find('.creator-attr'),
      creatorObject = {};

    $creatorAttrs.each(function() {
      creatorObject[$(this).data('creator-key')] = this.value;
    });

    $this.find('input[type="hidden"]').val(JSON.stringify(creatorObject));
  });

  // Binding for adding/removing creators
  $('.zotero-creator .add-creator').live('click', function() {
    var $oldCreator = $(this).parents('.zotero-creator'),
      $newCreator = $oldCreator.clone(true, true).insertAfter($oldCreator);
    $newCreator.find('textarea').val('').trigger('input');
  });

  $('.zotero-creator .remove-creator').live('click', function() {
    var $thisRow = $(this).parents('.zotero-creator');
    console.log($thisRow.siblings('.zotero-creator'));
    if ($thisRow.siblings('.zotero-creator').length) {
      $thisRow.remove();
    }
  });

  $('.collapsable').each(function() {
    var $legend = $(this);
    $legend
      .css('cursor', 'pointer')
      .append('<i style="margin: 6px 0 0 3px;" class="icon-minus"></i>')
      .click(function() {
        var $this = $(this).toggleClass('collapsed');
        $this.find('i').toggleClass('icon-plus icon-minus');
        $this.siblings('.collapse-content').toggle()
      });
    if ($legend.hasClass('collapse-on-show')) {
      $legend.trigger('click');
    }
  });

  $('select[name="item-type-select"]').change(function() {
    var $itemTypeSelect = $(this),
      itemType = $itemTypeSelect.val();
    if (itemType.length) {
      $.ajax({
        url: '/api/document/template/',
        data: {'itemType': itemType},
        success: function(data) {
          $itemTypeSelect
            .parents('.zotero-information')
            .replaceWith($(data).closest('.zotero-information'));
        }
      });
    }
  });

});
