$(document).ready(function() {

  var url = $.param.fragment();
  if ( url == '' ) {
    window.location.replace(window.location.href + '#note');
    url = $.param.fragment();
  }

  var tabs = $('#tabs a');

  tabs.click(function(e) {
    e.preventDefault();
    var index = $(this).attr('href').match(/#(.+)-tab/)[1];
    $.bbq.pushState(index, 2);
  });

  $(window).bind('hashchange', function(e) {
    var index = $.bbq.getState();
    $.each(index, function(key, value) {
      var tabToOpen = tabs.filter('a[href*="' + key + '"]');
      if (tabToOpen.length > 0) {
        tabToOpen.tab('show');
      }
    });
  }).trigger('hashchange');
});
