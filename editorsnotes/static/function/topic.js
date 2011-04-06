$(document).ready(function() {

  $('#collapse').jqcollapse({ slide: true, speed: 250, easing: '' });

  function update_facet(name) {
    var filters = [];
    $('#document-' + name + '-facet input:checked').each(function(index) {
      filters.push($(this).data('filter'));
    });
    if (filters.length == 0) {
      filters.push(false);
    }
    $('#document-list').isotope({ filter: filters.join(',') });
  }

  function init_facet(name) {
    var keys = [];
    var counts = {};
    $('#document-list .document').each(function(index) {
      var value = $(this).data(name);
      if (value == undefined) {
        value = 'None';
      }
      if (value in counts) {
        counts[value] += 1;
      } else {
        keys.push(value);
        counts[value] = 1;
      }
    });
    keys.sort();
    $.each(keys, function(index, value) {
      $('<li><label><input type="checkbox" checked/>' 
        + value + ' (' + counts[value] + ')</label></li>')
        .appendTo('#document-' + name + '-facet')
        .find(':checkbox')
        .data('filter', ((value == 'None') ? 
                         ':has(div.document:not(div[data-' + name + ']))' :
                         ':has(div.document[data-' + name + '="' + value + '"])'))
        .change(function() { update_facet(name); });
    });
  }

  init_facet('year');

  $('#tabs').tabs({
    show: function(event, ui) {
      if (ui.panel.id == 'documents') {
        $('#document-list').isotope({
          itemSelector: '.document-item',
          layoutMode: 'straightDown'
        });
      }
    },
  });
});
