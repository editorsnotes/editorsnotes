(function($) {
  $.fn.ellipsis = function(width) {
    return this.each(function(){
      var el = $(this);
      var t = $(this.cloneNode(true)).hide().css({
        'position': 'absolute',
        'width': 'auto',
        'overflow': 'visible',
        'max-width': 'inherit'
      });
      el.after(t);
      var words = t.text().split(' ');
      while(words.length > 0 && t.width() > width) {
        words.pop();
	t.html(words.join(' ') + ' &hellip;');
      }
      el.text(t.text());
      t.remove();
    });
  };
})(jQuery);