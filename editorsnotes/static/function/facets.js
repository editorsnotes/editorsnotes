(function($) {

  // Build the container for the facets
  var methods = {
    init: function() {
      return this.each(function(){
        var container = $(this),
          facetFields = ['itemtype', 'publicationtitle',
                         'author', 'recipient', 'archive'],
          allItems = container.find('.document'),
          initialFacets = facetObject(allItems, facetFields);
        container.data('facetFields', facetFields);
        container.data('allItems', allItems);
        container.data('initialFacets', initialFacets);

        $.each(facetFields, function(idx, key) {
          if (initialFacets[key]) {
            // Button to select this filter
            $('<li class="document-facet btn">')
              .data('for', key)
              .html('<i class="icon-plus"></i>' + key)
              .appendTo($selectors)

              // List of values for this filter
             $('<div class="facet-container span10">')
                .hide()
                .addClass(key + '-facet-container')
                .html('<h6>' + key + '</h6>')
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

          // Show/hide items
          if (!appliedFacets.length) {
            items.show();
          } else {
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
          $.each(facetFields, function(idx, facetKey) {
            var $filterList = $('.' + facetKey + '-facet-container ul'),
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
  },

  facetObject = function(items, facets) {
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
      $.each(facets, function() {
        var facetKey = this;
        if (data.hasOwnProperty(facetKey)){
          var facetVal = data[facetKey];
          if (!typeof(facetVal) == 'string') {
            $.each(facetVal, function() {
              f.pushFacetValue(facetKey, this, $this[0]);
            });
          } else {
            f.pushFacetValue(facetKey, facetVal, $this[0]);
          }
        }
      });
    });
    return f.fields;
  },

  $facetContainer = $('' +
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

    $('<h3 style="cursor: pointer;" id="facet-title">')
      .html('Filters <i style="vertical-align: baseline;" class="icon-minus"></i>')
      .bind('click', function() {
        $(this).find('i').toggleClass('icon-plus icon-minus');
        $container.toggle();
      }).appendTo($heading);


  $.fn.facet = function(method) {

    if (methods[method]) {
      return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
    } else if (typeof(method) === 'object' || !method) {
      return methods.init.apply(this, arguments);
    } else {
      $.error('Argument does not exist');
    }

  };
})(jQuery);
