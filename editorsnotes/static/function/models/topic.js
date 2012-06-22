$(document).ready(function() {

  var facetsInitiated = false;

  // If no hash is present in URL, load default tab into history
  var url = $.param.fragment();
  if ( url == '' ) {
    window.location.replace(window.location.href + '#article');
    url = $.param.fragment();
  }

  var tabs = $('#tabs a');

  tabs.click(function(e) {
    e.preventDefault();
    var index = $(this).attr('href').match(/#(.+)-tab/)[1];
    $.bbq.pushState(index, 2);
  }).on('shown', function(e) {
    var targetPanel = e.target.hash;
    if (targetPanel.match(/documents/)) {
      if (!facetsInitiated) {
        $('#document-list').facet();
        facetsInitiated = true;
      }
    }
  });

  $(window).bind('hashchange', function(e) {
    var index = $.bbq.getState();
    $.each(index, function(key, value) {
      var tabToOpen = tabs.filter('a[href*="' + key + '"]');
      if ( tabToOpen.length > 0 ) {
        tabToOpen.tab('show');
      }
    });
  }).trigger('hashchange');
});
