$(document).ready(function() {

  $('#collapse').jqcollapse({ slide: true, speed: 250, easing: '' });

  var facets = [ 'year', 'journal' ];

  function select_document_filters(facet_name) {
    var filters = [];
    $('#document-' + facet_name + '-facet input:checked').each(function(index) {
      filters.push($(this).data('filter'));
    });
    return $('#document-list').find(filters.join(',')).map(function() {
      return ':has(#' + this.id + ')';
    }).get();
  }

  function update_filter() {
    var selected = [];
    $.each(facets, function(index, value) {
      selected.push(select_document_filters(value));
    });
    var intersection = _.intersect.apply(this, selected);
    $('#document-list').isotope({ 
      filter: (intersection.length == 0 ? false : intersection.join(',')) });
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
        if (value != 'None') {
          keys.push(value);
        }
        counts[value] = 1;
      }
    });
    keys.sort();
    if ('None' in counts) {
      keys.push('None');
    }
    $.each(keys, function(index, value) {
      $('<li><label><input type="checkbox" checked/>' 
        + value + ' (' + counts[value] + ')</label></li>')
        .appendTo('#document-' + name + '-facet')
        .find(':checkbox')
        .data('filter', ((value == 'None') ? 
                         'div.document:not(div[data-' + name + '])' :
                         'div.document[data-' + name + '="' + value + '"]'))
        .change(function() { update_filter(); });
    });
  }

  $.each(facets, function(index, value) {
    init_facet(value);
  });

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
