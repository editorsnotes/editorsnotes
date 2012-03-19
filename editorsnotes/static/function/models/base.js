$(document).ready(function () {
  // Initialize timeago.
  $('time.timeago').timeago();

  $('#toggle-second-nav').click( function() {
    $(this).toggleClass('btn-primary');
    $('#bottom-nav').toggle();
  }); 

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
    source: function(request, response) {
      var targetModel = this.element.attr('search-target');
      if (targetModel == 'topics') {
        $.getJSON('/api/topics/', { q: request.term }, function(data) {
          response($.map(data, function(item, index) {
            return { label: item.preferred_name, uri: item.uri };
          }));
        });
      } else {
        // TODO: other models search complete
      }
    },
    minLength: 2,
    select: function(event, ui) {
      if (ui.item) {
        location.href = ui.item.uri;
      }
    }
  });
});
