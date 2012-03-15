$(document).ready(function() {

  var url = $.param.fragment();
  if ( url == '' ) {
    window.location.replace(window.location.href + '#note');
    url = $.param.fragment();
  }

  var tabs = $('#tabs a[data-toggle="tab"]');

  tabs.click(function() {
    var $thisTab = $(this);
    if (! $thisTab.parent().hasClass('active') ) {
      index = $(this).attr('href').substr(1);
      $.bbq.pushState(index, 2);
    }
  });

  $(window).bind('hashchange', function(e) {
    var index = $.bbq.getState();
    $.each(index, function(key, value) {
      var tabSearch = tabs.filter('a[href$="' + key + '"]');
      if ( tabSearch.length > 0 ) {
        tabSearch.tab('show');
      }
    });
  }).trigger('hashchange');
  
});
