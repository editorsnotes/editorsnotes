$(function() {
  
  $("#dialog-form").dialog({
    autoOpen: false,
    modal: true,
    width: 400
  });
  
  $("#dialog-form").keyup(function(){
    var keyLength = $("#zotero-key").val().length;
    var uidLength = $("#zotero-id").val().length;
    if (keyLength == 24 && uidLength == 6) {
      $("#dialog-form input[type='submit']").attr('disabled', false);  
    }
    else {
      $("#dialog-form input[type='submit']").attr('disabled', true);  
    };
  });
  
  $("#edit-zotero-info").click( function() {
    $("#dialog-form").dialog('open');
  });
  
});
