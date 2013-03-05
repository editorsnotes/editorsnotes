$(document).ready(function() {

  $('#zotero-information-edit').zotero({'description': '#id_description'});

  // Fall back to adding more file inputs if "multiple" attribute isn't supported
  if (!'multiple' in document.createElement('input')) {
    $('<div><a href="#" class="btn" id="add-scan">Add another scan</a></div>')
      .insertAfter('.scan-field .additional-scan')
      .css('margin-top', '1em')
      .on('click', '#add-scan', function(e) {
        var allInputs = $('.scan-field input[type="file"]'),
          lastInput = allInputs.last(),
          emptyInputs = allInputs.filter(function() { return this.value === '' });

        e.preventDefault();

        if (emptyInputs.length >= 5) {
          return;
        }

        $('<div class="additional-scan">')
          .insertAfter(lastInput.parents('.additional-scan'))
          .append( $('<input type="file">').attr('name', lastInput.attr('name')) );
      })
    .each(function() {
      var $btn = $('#add-scan', this);
      for (var i=0; i<4; i++) {
        $btn.trigger('click');
      }
    });
  }

});
