(function($) {

  $.fn.facet = function(method) {
    /*
     * Builds a form to facet items based on data attributes of elements. Accepts
     * either strings or arrays of strings as values.
     *
     * Usage:
     * $someContainer.facet({
     *   fields = [ {'key': 'facetA', 'label': 'First Facet Label'},
     *              {'key': 'facetB', 'label': 'Second Facet Label'}, ... ]
     *   itemSelector = '.elements-with-data-atts'
     * });
     *
     */
    var methods = {

      init: function( options ) {

        if (!options.fields) {
          console.log('Provide a list of fields to facet on');
          return;
        }
        if (!options.itemSelector) {
          console.log('Provide a selector for the items to be faceted.');
          return;
        }

        return this.each(function(){
          var container = $(this),
            facetFields = options.fields;
            allItems = container.find(options.itemSelector),
            initialFacets = facetObject(allItems, facetFields);
          container.data('facetFields', facetFields);
          container.data('allItems', allItems);
          container.data('initialFacets', initialFacets);

          // The container for the facets
          var $facetContainer = $('' +
            '<div id="facets" class="row">' +
              '<div id="facet-heading" class="span12"></div>' +
              '<div id="facet-container">' +
                '<div class="span2" id="available-facets">' +
                  '<ul class="unstyled">' +
                  '</ul>' +
                '</div>' +
                '<div class="span10 roow" id="facet-inputs">' +
                '</div>' +
              '</div>' +
            '</div>'),
            $heading = $facetContainer.find('#facet-heading');
            $container = $facetContainer.find('#facet-container'),
            $selectors = $facetContainer.find('ul'),
            $values = $facetContainer.find('#facet-inputs');

          // Show/hide the container
          $('<h3 style="cursor: pointer;" id="facet-title">')
            .html('Filters <i style="vertical-align: baseline;" class="icon-minus"></i>')
            .bind('click', function() {
              $(this).find('i').toggleClass('icon-plus icon-minus');
              $container.toggle();
            }).appendTo($heading);


          $.each(facetFields, function() {
            var facetKey = this.key,
              facetLabel = this.label;
            if (initialFacets[facetKey]) {
              // Button to select this filter
              $('<li class="document-facet btn">')
                .data('for', facetKey)
                .html('<i class="icon-plus"></i>' + facetLabel)
                .appendTo($selectors)

                // List of values for this filter
               $('<div class="facet-container span10">')
                  .hide()
                  .addClass(facetKey + '-facet-container')
                  .html('<h6>' + facetLabel + '</h6>')
                  .appendTo($values)
                  .append('<ul class="unstyled">');
            }
          });

          $facetContainer.insertBefore(container);

          $('.facet-input').live('click', function() {
            container.facet('update')
          });
          $('.document-facet').live('click', function() {
            var $filter = $(this),
              criteria = $filter.data('for'),
              target = $('.' + criteria + '-facet-container').toggle();
            $filter
              .toggleClass('document-facet-selected btn-primary')
              .find('i')
                .toggleClass('icon-plus icon-minus icon-white');
            if (!$filter.hasClass('document-facet-selected')) {
              target.find('input')
                .prop('checked', false)
                .filter(':first')
                .trigger('click');
            }
          });

          container.facet('update');
        });
      },

      // Update form to reflect the selected inputs
      update: function() {
        return this.each(function(){

          var container = $(this),
            items = container.data('allItems'),
            facetFields = container.data('facetFields'),
            facets = facetObject(items, facetFields),
            itemsToShow = [],
            checkedInputs = $('.facet-input:checked'),
            appliedFacets = checkedInputs.map(function() {
              return [ facets[this.name][this.value] ];
            });

            // Show/hide items before creating new facet values
            if (!appliedFacets.length) {
              // Show all items if not facets are selected
              items.show();
            } else {
              // Otherwise, find all items that match the given criteria.
              // There may be a better way to do this, but for now, this looks
              // at the first field faceted on, finds the items that match
              // that restraint, and then checks each of the other applied
              // restraints, hiding all elements that don't apply.
              //
              // In effect this is just doing a union of the different arrays
              // of items generated by the facet criteria.

              var comparisons = appliedFacets.slice(1);
              $.each(appliedFacets[0], function(idx, item) {
                var inTheRest = true;
                $.each(comparisons, function() {
                  if (this.indexOf(item) == -1) {
                    inTheRest = false;
                  }
                });
                if (inTheRest) {
                  itemsToShow.push(item);
                }
              });
              items.hide();
              $(itemsToShow).show();
            }

            facets = facetObject(items.filter(':visible'), facetFields),
          
            // Inputs from facets
            $.each(facetFields, function() {
              var facetKey = this.key,
                $filterList = $('.' + facetKey + '-facet-container ul'),
                thisFacet = facets[facetKey] || [],
                facetLength = 0;
              $filterList.children().remove();
              $.each(thisFacet, function(item, arr) {
                facetLength += 1;
                var $item = $('<li>')
                  .appendTo($filterList)
                  .html('&nbsp;' + item + ' (' + arr.length + ')')
                $('<input class="facet-input" type="checkbox">')
                  .attr('name', facetKey)
                  .val(item)
                  .prependTo($item)
              });
              if (!facetLength) {
                $('<span class="quiet">(no values)</span>').appendTo($filterList);
              }
            });
            
            $.each(checkedInputs, function() {
              $('.facet-input[name="' + this.name + '"][value="' + this.value + '"]')
                .prop('checked', true);
            });

        });
      }
    };

    var facetObject = function(items, facetFields) {
      var f = {};
      f.fields = {};
      f.pushFacetValue = function(field, k, v) {
        // Default values for undefined keys
        f.fields[field] = f.fields[field] || {};
        f.fields[field][k] = f.fields[field][k] || [];
        f.fields[field][k].push(v);
      };
      $.each(items, function() {
        var $this = $(this),
          data = $this.data();
        $.each(facetFields, function() {
          var facetKey = this.key;
          if (data.hasOwnProperty(facetKey)){
            var facetVal = data[facetKey];
            if (facetVal.substr(0,2) == "['" && facetVal.substr(-2) == "']") {
              facetVal = facetVal.slice(1,-1).split(/, ?/).map(function(a) { return a.slice(1,-1) });
            }
            if (facetVal instanceof Array) {
              $.each(facetVal, function() {
                f.pushFacetValue(facetKey, this, $this[0]);
              });
            } else if (typeof(facetVal) == 'string') {
              f.pushFacetValue(facetKey, facetVal, $this[0]);
            }
          }
        });
      });
      return f.fields;
    };


    if (methods[method]) {
      return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
    } else if (typeof(method) === 'object' || !method) {
      return methods.init.apply(this, arguments);
    } else {
      $.error('Argument does not exist');
    }

  };
})(jQuery);
