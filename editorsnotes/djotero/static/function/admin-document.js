$(document).ready(function() {
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

  var autocompletePrefs = {
    source: function(request, response) {
      var $searchBox = this.element;
      $.getJSON('/api/topics/', {'q': request.term}, function(data) {
        if (!data.length) {
          $searchBox
            .trigger('autocompleteopen')
          return response(false);
        }
        else {
          response($.map(data, function(item, index) {
            return { id: item.id, label: item.preferred_name, uri: item.uri };
          }));
        }
      });
    },
    minLength: 2,
    position: {
      my: 'left bottom',
      at: 'left top'
    },
    select: function(event, ui) {
      var $this = $(event.target).val(''),
        $oldExtraField = $this.parents('.control-group'),
        $newExtraField = $oldExtraField.clone(),
        oldFieldCounter,
        newFieldCounter;

      // Create a new extra field
      oldFieldCounter = parseInt(
        $oldExtraField
          .find('input[type="hidden"]')
          .attr('name')
          .match(/\d+/)[0]);
      newFieldCounter = oldFieldCounter + 1;
      $newExtraField.find('input').each(function() {
        var $this = $(this);
        if ($this.attr('name')) {
          $this.attr('name', $this.attr('name').replace(oldFieldCounter, newFieldCounter));
        }
        if ($this.attr('id')) {
          $this.attr('id', $this.attr('id').replace(oldFieldCounter, newFieldCounter));
        }
      });
      $newExtraField.find('.topic-autocomplete').autocomplete(autocompletePrefs);
      $newExtraField.insertAfter($oldExtraField);

      // Update management form to reflect new number of fields
      $oldExtraField.siblings('input[name$=TOTAL_FORMS]').val(newFieldCounter + 1);

      // Replace this input with a text field
      $oldExtraField.find('input[name$=topic]').val(ui.item.id);
      $oldExtraField.find('label').remove();
      $this.replaceWith(ui.item.label);
    }
  }

  $('#document-related-topics-edit')
    .on('click', '.remove-related-topic', function() {
      $(this)
        .siblings('input[name$="DELETE"]').attr('checked', true)
        .parents('.control-group').fadeOut('slow');
      return false;
    })
    .on('autocompletecreate', '.topic-autocomplete', function(event) {
      var $searchBox = $(event.target),
        $ajaxLoader = $('<img class="loading" src="/static/style/icons/ajax-loader.gif">');
      $ajaxLoader.css('margin-left', '4px').insertAfter($searchBox).hide();
    })
    .on('autocompletesearch', '.topic-autocomplete', function(event) {
      $(event.target).siblings('img').show();
    })
    .on('autocompleteopen', '.topic-autocomplete', function(event) {
      $(event.target).siblings('img').hide();
    })
    .find('input[name$="DELETE"]').each(function() {
      $checkbox = $(this),
        $group = $checkbox.parents('.control-group'),
        $removeButton = $('<a class="remove-related-topic" href="#">');
      $removeButton
        .html('<i class="icon-remove-sign"></i>')
        .appendTo($group);
      $checkbox.hide();
    });

  $('.topic-autocomplete').autocomplete(autocompletePrefs);

});
