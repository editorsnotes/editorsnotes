$(function() {
  $('#dialog-form :input[type="text"]').attr('readonly', false);
  
  $("#dialog-form").dialog({
    autoOpen: false,
    modal: true,
    width: 400
  });
  
  $("#test-zotero-information").live('click', function(){
    var loader = $('<img src="/media/style/icons/ajax-loader.gif">');
    var button = $(this).replaceWith(loader);
    $.ajax({
      url: '/document/upload/access',
      data: {
        validate: "1",
        zotero_uid: $("#zotero-id").val(),
        zotero_key: $("#zotero-key").val()
      },
      success: function() {
        validationSuccess = 1;
        $(loader).remove();
        $("#test-message").html('<p>Combination OK!</p>');
        $('#dialog-form :input[type="text"]').attr('readonly', true).css('background', '#EEEEEE');
        $("#dialog-form input[type='submit']").attr('disabled', false).show();
      },
      error: function() {
        $(loader).replaceWith(button);
        $("#test-message").html('<p>Combination invalid, make sure that the ID and Key are entered correctly and that they key provides read access.</p>');
      }
    });
  });
  
  $("#edit-zotero-info").click( function() {
    $("#dialog-form").dialog('open');
    if ( typeof validationSuccess == "undefined") {
      $('#dialog-form :input[type="text"]').val("");
      $('#test-message').html('');
    }
    else {
    }
  });
  
});
