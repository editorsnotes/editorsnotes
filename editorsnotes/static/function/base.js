$(document).ready(function () {
  // Initialize timeago.
  $('time.timeago').timeago();

  $('#toggle-second-nav').click( function() {
    $(this).toggleClass('btn-primary');
    $('#bottom-nav').toggle();
  }); 

  var truncateChars = function(text, l) {
    if (typeof(l) == 'undefined') {
      var l = 100;
    }
    if (text.length > l) {
      return text.substr(0, l/2) + ' ... ' + text.substr(-(l/2));
    }
    else {
      return text;
    }
  }

  // Initialize autocomplete for search input box.
  $('input.search-autocomplete')
  .keydown(function(event) {
    // If no autocomplete menu item is active, submit on ENTER.
    if (event.keyCode == $.ui.keyCode.ENTER) {
      if ($('#ui-active-menuitem').length == 0) {
        $('#searchform form').submit();
      }
    }
  })
  .autocomplete({
    source: function(request, response, x) {
      var targetModel = this.element.attr('search-target'),
        query = {'q': request.term};

      if (this.element.attr('search-project-id')) {
        query['project_id'] = this.element.attr('search-project-id');
      }

      switch (targetModel) {
        case 'topics':
          $.getJSON('/api/topics/', query, function(data) {
            response($.map(data, function(item, index) {
              return { id: item.id, label: truncateChars(item.preferred_name), uri: item.uri };
            }));
          });
          break;

        case 'notes':
          $.getJSON('/api/notes/', query, function(data) {
            response($.map(data, function(item, index) {
              return { id: item.id, label: truncateChars(item.title), uri: item.uri };
            }));
          })
          break;

        case 'documents':
          $.getJSON('/api/documents/', query, function(data) {
            response($.map(data, function(item, index) {
              return { id: item.id, label: truncateChars(item.description), uri: item.uri };
            }));
          })
          break;
      }
    },
    minLength: 2,
    select: function(event, ui) {
      var $this = $(event.target);
      if (ui.item && !$this.hasClass('autocomplete-no-redirect')) {
        location.href = ui.item.uri;
      } else if (ui.item) {
        $this.attr('disabled', 'disabled');
        $('<input type="hidden">').attr({
          'name': 'autocomplete-model',
          'value': $this.attr('search-target')
        }).insertAfter($this);
        $('<input type="hidden">').attr({
          'name': 'autocomplete-id',
          'value': ui.item.id
        }).insertAfter($this);

        $('<i class="icon-remove-sign clear-search">')
          .insertAfter($this)
          .click(function() {
            var $this = $(this);
            $this.prev('input.search-autocomplete')
              .removeAttr('disabled')
              .val('')
              .siblings('input[type="hidden"][name^="autocomplete-"]').remove();
            $this.remove();
          });
      }
    }
  });
});
