$(function() {

  var splitColumns = function(documentArray) {
    var $sortedNotes;
    var $sortOption = $('.sort-option-selected');
    var sortBy = $sortOption.attr('data-sort-by');

    if (sortBy == 'title') {
      $sortedNotes = _.sortBy(documentArray, function(doc) {
        return doc.textContent.replace(/[^\w ]/g, '')
      });
    }
    if ($sortOption.attr('data-sort-order') == 'desc') {
      $sortedNotes = $.makeArray($sortedNotes).reverse();
    }
    $('#document-list').append($sortedNotes);
  }
  var $facets = $('#document-facets input');
  $facets.prop('checked', false);
  $facets.live('click', function() {
    var $checked = $('#document-facets input:checked');
    var $sortingOptions = $('.sort-option');
    var queryString = '?filter=1'
    var filter = {};

    $.each($checked, function(key, val) {
      if (!filter.hasOwnProperty(val.name)) {
        filter[val.name] = [];
      }
      filter[val.name].push(val.value);
    });
    console.log(filter);
    $.each(filter, function(key, val) {
      if (val.length > 0) {
        queryString += ('&' + key + '=' + val.join('|'))
      }
    });
    $.get(queryString, function(data) {
      $('#all-documents').html(data);

      // Restore previously checked filters
      $.each($checked, function(key, val) {
        $('#document-facets input[name="' + val.name + '"][value="' + val.value + '"]')
          .prop('checked', true);
      });

      // Restore previous sort options
      $.each($sortingOptions, function(key, val) {
        var $oldOption = $(val);
        var $newOption = $('.sort-option[sort-by="' + $oldOption.attr('sort-by') + '"]');
        $newOption.replaceWith($oldOption);
      });
    });
  });
  
  
  // Toggle faceting options
  $('.facet-title').live('click', function() {
    $(this).find('i').toggleClass('icon-plus icon-minus');
    $('.facets').slideToggle('fast');
  })

  // Resort list of notes on click of sort options
  $('.sort-option').live('click', function() {
    var $thisOption = $(this);
    var $otherOptions = $thisOption.siblings('.sort-option');

    if ($thisOption.hasClass('sort-option-selected')) {
      $thisOption.find('i').toggleClass('icon-chevron-up icon-chevron-down');
      if ($thisOption.attr('data-sort-order') == 'asc') {
        $thisOption.attr('data-sort-order', 'desc');
      } else {
        $thisOption.attr('data-sort-order', 'asc');
      }
    } else {
      $otherOptions.removeClass('sort-option-selected');
      $thisOption.addClass('sort-option-selected');
    }

    $('.timeago-label').remove();
    splitColumns($('.document'));
  });

});
