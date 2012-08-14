$(document).ready(function() {

  $('form')
    // Warn users who have not saved changes before leaving page
    .one('change', function() {
      window.onbeforeunload = function() {
        return 'You have not saved your changes.';
      };
    })
    // ..but not when next page is triggered by clicking save
    .on('submit', function() {
      window.onbeforeunload = null;
    })

    // Allow fields to be collapsed to save space
    .on('click', '.collapsable legend', function() {
      var $this = $(this);
      $this.toggleClass('.collapsed')
        .find('i').toggleClass('icon-plus icon-minus');
      $this.siblings('.fieldset-content').toggle();
    })

    // When icon to remove topic is clicked, check the corresponding
    // 'DELETE' checkbox & hide the item.
    .on('click', '.remove-related-topic', function(event) {
      event.preventDefault();
      $(this)
        .siblings('input[name$="DELETE"]').attr('checked', true)
        .parents('.control-group').fadeOut('slow');
    });


  // Add icons for fieldset collapsing & trigger click on fields to be
  // hidden by default
  $('.collapsable legend')
    .css('cursor', 'pointer')
    .each(function() {
      $('<i>', {
        'class': 'icon-minus',
        'css': {'margin': '6px 0 0 3px'}
      }).appendTo(this);
    })
    .filter('.collapse-on-show').trigger('click');

  $('.related-topic input[name$="DELETE"]').each(function() {
    $('<a>', {
      'class': 'remove-related-topic',
      'href': '#',
      'html': '<i class="icon-remove-sign"></i>'
    }).appendTo( $(this).hide().parents('.control-group') );
  });

  $('<input type="text" placeholder="Add topic (type to search)">')
    .on('change input', function(event) {
      // Don't trigger change or input events when typing into this field,
      // since it's just used for autocomplete & won't be saved
      event.stopPropagation();
    })
    .appendTo('.related-topics-field .fieldset-content')
    .after($('<img>', {
      id: 'related-topics-loading',
      src: '/static/style/icons/ajax-loader.gif',
      css: {'margin-left': '4px','display': 'none'}
    }))
    .autocomplete({
      source: function(request, response) {
        $.ajax({
          url: '/api/topics/',
          dataType: 'json',
          data: {'q': request.term},
          beforeSend: function() {
            $('#related-topics-loading').css('display', 'inline-block');
          },
          success: function(data) {
            response($.map(data, function(item, index) {
              return { id: item.id, label: item.preferred_name, uri: item.uri };
            }));
          },
          complete: function() {
            $('#related-topics-loading').hide();
          }
        });
      },
      minLength: 2,
      position: {
        my: 'left bottom',
        at: 'left top'
      },
      select: function(event, ui) {
        var $oldExtraField = $('.related-topic:last').trigger('change'),
          $newExtraField = $oldExtraField.clone().insertAfter($oldExtraField),
          oldFieldCounter,
          newFieldCounter;

        // Create a new extra field
        oldFieldCounter = $oldExtraField
          .find('input[type="hidden"]')
          .attr('name')
          .match(/\d+/)[0];
        oldFieldCounter = parseInt(oldFieldCounter);
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

        // Update management form to reflect new number of fields
        $oldExtraField
          .parents('fieldset')
          .find('input[name$=TOTAL_FORMS]')
            .val(newFieldCounter + 1);

        // Replace this input with a text field
        $oldExtraField
          .prepend(ui.item.label)
          .find('input[name$=topic]').val(ui.item.id);

        // Clear this input
        event.preventDefault();
        $(this).val('').blur();

      }
    });

});
