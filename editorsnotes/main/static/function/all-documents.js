$(function() {
  var $facets = $('#facets');
  var selectedFacets = []

  $('body')
    .on('click', '#facets.loaded .facets-available li', function () {
      var $this = $(this).toggleClass('facet-selected')
        , criteria = $this.data('facet-toggle')
        , $target = $('.select-facets-' + criteria, $facets);

      $target.toggle();
      if ($this.hasClass('facet-selected')) {
        if (selectedFacets.indexOf(criteria) === -1) {
          selectedFacets.push(criteria);
        }
      } else {
        selectedFacets.pop(criteria);
        $('input:checked', $target)
          .prop('checked', false)
          .filter(':first')
            .trigger('click');
      }
      $('i', $this).toggleClass('icon-plus icon-minus');
    })
    .on('click', '#facets .facet-header', function () {
      $('i', this).toggleClass('icon-plus icon-minus');
      $('.facet-body').toggle();
    })
    .on('click', '#facets .facet-form input', function () {
      var $inputs = $('input', $facets)
        , $checkedInputs = $inputs.filter(':checked')
        , queryParams = {}

      $.each($checkedInputs, function() {
        if (!queryParams.hasOwnProperty(this.name)) {
          queryParams[this.name] = [];
        }
        queryParams[this.name].push(this.value);
      });

      $inputs.prop('disabled', true);
      $facets.removeClass('loaded');

      $.ajax({
        type: 'GET',
        url: '?filter=1',
        data: queryParams,
        success: function(data) {
          var newdoc = $('#all-documents').html(data)
            , prevSelectedFacets = selectedFacets.slice(0);

          $facets = $('#facets', newdoc);

          // Restore previously selected facets
          console.log(prevSelectedFacets);
          for (var i = 0; i < prevSelectedFacets.length; i++) {
            var selector = 'li[data-facet-toggle="' + prevSelectedFacets[i] + '"]'
            $(selector, $facets).trigger('click');
          }

          // Restore previously checked boxes
          $checkedInputs.each(function() {
            var selector = '[name="' + this.name + '"][value="' + this.value + '"]'
            $('input' + selector, $facets).prop('checked', true)
          });

        },
        error: function() {
          $inputs.prop('disabled', false);
          alert('Error processing query');
        }
      });

    });

});
