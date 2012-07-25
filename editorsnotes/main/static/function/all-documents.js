$(function() {
  
  // Toggle filter menu
  $('#facet-title').live('click', function() {
    $(this).find('i').toggleClass('icon-plus icon-minus');
    $('#filter-selection').toggle();
  });


  // Add filter criteria
  $('#filters.loaded .document-filter').live('click', function() {
    var $filter = $(this).toggleClass('document-filter-selected btn-primary'),
      criteria = $filter.attr('for'),
      target = $('.' + criteria + '-filter').toggle();
    if (!target.is(':visible')) {
      target.find('input:checked')
        .prop('checked', false)
        .filter(':first')
          .trigger('click');
    }
    $filter
      .find('i').toggleClass('icon-plus icon-minus icon-white');
  });


  // Apply selected filter criteria
  $('#filter-form input').live('click', function() {
    var $inputs = $('#filter-form input'),
      $checkedInputs = $inputs.filter(':checked'),
      $selectedFilters = $('.document-filter-selected'),
      queryParams = {};
    
    // Build the query to be passed
    $.each($checkedInputs, function() {
      if (!queryParams.hasOwnProperty(this.name)) {
        queryParams[this.name] = [];
      }
      queryParams[this.name].push(this.value);
    });

    // Lock inputs until request can be processed
    $inputs.prop('disabled', true);
    $('#filters').removeClass('loaded');

    // Ajax request for results
    $.ajax({
      type: 'GET',
      url: '?filter=1',
      data: queryParams,
      success: function(data) {

        $('#all-documents').html(data);

        // Restore previously selected filters
        $.each($selectedFilters, function() {
          var filterCriteria = $(this).attr('for');
          $('#available-filters li[for="' + filterCriteria + '"]')
            .trigger('click');
        });

        // Restore previously checked boxes
        $.each($checkedInputs, function() {
          var selector = '#filter-form input' +
            '[name="' + this.name + '"]' +
            '[value="' + this.value + '"]';
          $(selector).prop('checked', true);
        });

      },
      error: function() {
        $inputs.prop('disabled', false);
        alert('Error processing query');
      }
    });

  });

});
