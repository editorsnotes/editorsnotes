$(function() {
  
  $("#dialog-form").dialog({
    autoOpen: false,
    modal: true,
    width: 400
  });
  
  $("#test-zotero-information").live('click', function(){
      var button = $(this).replaceWith('<img class="loading-image" src="/media/style/icons/ajax-loader.gif">');
      $.ajax({
        url: '/document/upload/access',
        data: {
          validate: "1",
          zotero_uid: $("#zotero-id").val(),
          zotero_key: $("#zotero-key").val()
        },
        success: function() {
          $(".loading-image").remove();
          $("#test-message").html('<p>Name and key OK!</p>');
          $("#dialog-form input[type='submit']").attr('disabled', false).show();
        },
        error: function() {
          $(".loading-image").replaceWith(button);
          $("#test-message").html('<p>Combination invalid, make sure that the ID and Key are entered correctly and that they key provides read access.</p>');
        }
      });
  });
  
  $("#edit-zotero-info").click( function() {
    $("#dialog-form").dialog('open');
  });
  
});
