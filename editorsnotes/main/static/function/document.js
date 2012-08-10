Seadragon.Config.proxyUrl = '/proxy?url='
Seadragon.Config.imagePath = '/static/function/seadragon/img/'
$(document).ready(function() {

  // Parse URL params.
  var url_params = {};
  (function () {
    var e,
        a = /\+/g,  // Regex for replacing addition symbol with a space
        r = /([^&=]+)=?([^&]*)/g,
        d = function (s) { return decodeURIComponent(s.replace(a, " ")); },
        q = window.location.search.substring(1);
    while ((e = r.exec(q))) {
      url_params[d(e[1])] = d(e[2]);
    }
  })();

  // Scan processing monitor for progress bar.
  var monitor = {
    init: function(viewer, url) {
      this.stop_polling(this);
      this.viewer = viewer;
      this.url = url;
      $('#progressbar').progressbar('option', 'value', 0);
    },
    start: function() {
      this.check(this);
    },
    check: function(self) {
      $.ajax({
        url: self.url,
        dataType: 'jsonp',
        success: function(data) {
          var o = data.content ? data.content : data;
          if (o.ready && o.dzi) {
            self.stop_polling(self);
            $('#progress-notify').hide();
            self.viewer.openDzi(o.dzi.url);
          } else if (o.failed) {
            self.abort(self, o.url + ' failed to convert: ' + o.shareUrl);
          } else {
            var percent = Math.round(100 * o.progress);
            $('#progress-notify').show();
            $('#progressbar').progressbar('option', 'value', percent);
            if (data.redirectLocation) {
              self.url = data.redirectLocation;
              self.start_polling(self);
            }
          }
        },
        error: function(request, status) {
          self.abort(self, 'HTTP request failed: ' + status);
        }
      });
    },
    start_polling: function(self) {
      if (! self.interval_id) {
        self.interval_id = window.setInterval(
          function() { self.check(self); }, 1000);
      }
    },
    stop_polling: function(self) {
      if (self.interval_id) {
        window.clearInterval(self.interval_id);
      }
      self.interval_id = null;
    },
    abort: function(self, message) {
      self.stop_polling(self);
      console.log(message);
      $('#progress-message').text('Oops! Something broke. Please reload the page.').css('color', 'red');
    }
  };

  // Footnote interface for transcripts.
  var footnote = {
    done: false,
    width: 800,
    display: null,
    setup: function() {
      if (footnote.done) { return; }
      footnote.done = true;
      var footnotes = $('a.footnote');
      footnotes.click(function (event) { event.preventDefault(); });
      var i = 1;
      footnotes.each(function() {
        var a = $(this),
            noteid = 'note-' + a.attr('href').split('/')[2],
            punc = '',
            text,
            number;
        if (a[0].nextSibling && a[0].nextSibling.nodeType == 3) { // text node
          text = $(a[0].nextSibling).text();
          if (text.length > 0 && (text[0] == ',' || text[0] == '.')) {
            punc = text[0];
            $(a[0].nextSibling).replaceWith(
              $(document.createTextNode(text.slice(1))));
          }
        }
        number = $(document.createElement('span'));
        number.addClass('footnote-number');
        number.html(punc + '<small><sup>' + i + '</sup></small>');
        a.after(number);
        number.hover(function() { a.hover(); });
        a.popover({
          placement: function (pop, a) {
            var a_offset = $(a).offset(),
                a_width = $(a).width(),
                a_x, a_y;
            a_x = a_offset.left - $('body').scrollLeft() + (a_width / 2); 
            if (a_x < 300) { return 'right'; }
            if (a_x > $(window).width() - 300) { return 'left'; }
            a_y = a_offset.top - $('body').scrollTop();
            return (a_y > $(window).height() / 2) ? 'top' : 'bottom';
          },
          title: i + '. ' + a.text(),
          content: $('#' + noteid).html()
        });
        i += 1;
      });
    }
  }

  // Main routine starts here  --------------------------------------------------

  $('#scan-viewer').each(function() {
    // Initialize scan viewer.
    var viewer = new Seadragon.Viewer(this);

    // Handle scan button clicks.
    $('a.scan').click(function(event) {
      event.preventDefault();

      $('a.btn-info').removeClass('btn-info');
      $(this).addClass('btn-info');
      viewer.close();
      monitor.init(viewer, 'http://api.zoom.it/v1/content/?url=' + encodeURIComponent(this.href));
      monitor.start();
    });
  });

  // If no hash is present in URL, load default tab into history
  var url = $.param.fragment();
  if ( url == '' ) {
    window.location.replace(window.location.href + '#info');
    url = $.param.fragment();
  }

  var tabs = $('#tabs a');
  
  // Initialize tabs & jquery-bbq
  tabs.click(function(e) {
    e.preventDefault();
    var index = $(this).attr('href').match(/#(.+)-tab/)[1];
    $.bbq.pushState(index, 2);
  }).on('shown', function(e) {
    var targetPanel = e.target.hash;
    if (targetPanel.match(/scans/)) {
      if ($('a.pushed').click().length == 0) {
        $('a.scan:first').click();
      }
      if ($('#progress-notify') && !monitor.initialized) {
        $('#progressbar').progressbar({ value: 0 });
        $('#progress-notify').position({
          of: '#scan-viewer',
          my: 'center center',
          at: 'center center'
        }).hide();
        monitor.initialized = true;
      }

    } else if (targetPanel.match(/transcript/)) {
      var firstshow = (! footnote.done);
      footnote.setup();
      if (firstshow && 'fn' in url_params) {
        var fn = $('a.footnote[href="/footnote/' + url_params.fn + '/"]');
        if (fn.length == 1) {
          window.setTimeout(function() {
            $('html,body').scrollTop(fn.offset().top - 10);
          }, 100);
        }
      }
    }
  });

  $(window).bind('hashchange', function(e) {
    var index = $.bbq.getState();
    $.each(index, function(key, value) {
      var tabToOpen = tabs.filter('a[href*="' + key + '"]')
      if ( tabToOpen.length > 0 ) {
        tabToOpen.tab('show');
      }
    });
  }).trigger('hashchange');
});
