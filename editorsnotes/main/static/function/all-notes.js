$(function() {

  var groupDates = function(noteArray, order) {
    var compareDate = function(d) {
      // Compare the array with the given date and return the first match 
      var monthstr = '' + (d.getMonth() + 1);
      var daystr = '' + d.getDate();
      while (monthstr.length < 2) monthstr = '0' + monthstr;
      while (daystr.length < 2) daystr = '0' + daystr;
      var testDate = d.getFullYear() + monthstr + daystr;
      var dateMatch = _.find(noteArray, function(note) {
        var noteDate = note.getAttribute('date-modified')
          .slice(0,10).replace(/-/g, '')
        return noteDate < testDate;
      });
      return dateMatch;
    }
    var insertlabel = function(note, labelDate) {
      // Insert a label into the note array to visually group time periods
      var timeAgoText = $.timeago(labelDate)
        .replace('about ', '')
        .replace(/\d+ hours/, 'a day');
      var $label = $('<li class="timeago-label">');
      if (order == 'desc') {
        var labelText = '<h4>Edited more than ' + timeAgoText + '</h4>';
        $label.html(labelText).insertBefore($(note));
        if ($label.prev().hasClass('timeago-label')) {
          $label.prev().remove();
        }
      } else if (order == 'asc') {
        var labelText = '<h4>Edited less than ' + timeAgoText + '</h4>';
        $label.html(labelText).insertAfter($(note));
        if ($label.next().hasClass('timeago-label')) {
          $label.next().remove();
        }
      }
    }

    var today = new Date;
    var ty = today.getFullYear(),
        tm = today.getMonth(),
        td = today.getDate();
    var datesToCompare = [
      new Date(ty, tm, td),
      new Date(ty, tm, td-7),
      new Date(ty, tm, td-14),
      new Date(ty, tm, td-31),
      new Date(ty, tm-3, td),
      new Date(ty, tm-6, td)
    ]

    if (order == 'asc') {
      noteArray = $.makeArray(noteArray).reverse();
      datesToCompare.reverse();
    } else if (order == 'desc') {
      $('<li class="timeago-label"><h4>Edited Today</h4></li>').insertBefore(_.first(noteArray));
    }
    
    $.each(datesToCompare, function(counter, dateToTest) {
        insertlabel(compareDate(dateToTest), dateToTest);
    });

    // Keep adding labels for years ago until upper limit is reached
    var yearsAgo = 1;
    while (yearsAgo > 0) {
      var dateToTest = new Date(ty-yearsAgo, tm, td);
      var dateMatch = compareDate(dateToTest);
      if (dateMatch) {
        insertlabel(dateMatch, dateToTest);
        yearsAgo++;
      } else {
        // Put final label at top if needed
        if (order == 'asc') {
          var labelText = '<h4>Edited less than ' + $.timeago(dateToTest).replace('about ', '') + '</h4>';
          $('<li class="timeago-label">').html(labelText).insertBefore(_.last(noteArray));
        }
        yearsAgo = 0;
      }
    }
  }

  var splitColumns = function(noteArray) {
    var $sortedNotes;
    var $sortOption = $('.sort-option-selected');
    var sortBy = $sortOption.attr('sort-by');

    if (sortBy == 'title') {
      $sortedNotes = _.sortBy(noteArray, function(note) {
        return note.textContent
      });
    } else if (sortBy == 'date') {
      $sortedNotes = _.sortBy(noteArray, function(note) {
        return note.getAttribute('date-modified')
      });
    }
    if ($sortOption.attr('sort-order') == 'desc') {
      $sortedNotes = $.makeArray($sortedNotes).reverse();
    }

    $('#note-list-1').append($sortedNotes);
    if ($sortedNotes.length > 20) {
      $('#note-list-2').append($sortedNotes.slice($sortedNotes.length/2));
    }
    if (sortBy == 'date') {
      groupDates($('.note'), $sortOption.attr('sort-order'));
    }
  }

  var $facets = $('#note-facets input');
  $facets.prop('checked', false);
  $facets.live('click', function() {
    var $checked = $('#note-facets input:checked');
    var $sortingOptions = $('.sort-option');
    var queryString = '?filter=1'
    var filter = {project : [], topic: [], note_status: []}

    $.each($checked, function(key, val) {
      filter[val.name].push(val.value);
    });

    $.each(filter, function(key, val) {
      val.forEach(function (v) {
        queryString += ('&' + key + '=' + encodeURIComponent(v))
      });
    });
    $.get(queryString, function(data) {
      $('#all-notes').html(data);

      // Restore previously checked filters
      $.each($checked, function(key, val) {
        $('#note-facets input[name="' + val.name + '"][value="' + val.value + '"]')
          .prop('checked', true);
      });

      // Restore previous sort options
      $.each($sortingOptions, function(key, val) {
        var $oldOption = $(val);
        var $newOption = $('.sort-option[sort-by="' + $oldOption.attr('sort-by') + '"]');
        $newOption.replaceWith($oldOption);
      });

      splitColumns($('.note'));
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
      if ($thisOption.attr('sort-order') == 'asc') {
        $thisOption.attr('sort-order', 'desc');
      } else {
        $thisOption.attr('sort-order', 'asc');
      }
    } else {
      $otherOptions.removeClass('sort-option-selected');
      $thisOption.addClass('sort-option-selected');
    }

    $('.timeago-label').remove();
    splitColumns($('.note'));
  });
  
  // Split columns on load
  splitColumns($('.note'));

});
