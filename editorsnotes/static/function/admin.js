$(document).ready(function () {

  var wymconfig = {
    skin: 'custom',
    toolsItems: [
      {'name': 'Bold', 'title': 'Strong', 'css': 'wym_tools_strong'}, 
      {'name': 'Italic', 'title': 'Emphasis', 'css': 'wym_tools_emphasis'},
      {'name': 'InsertOrderedList', 'title': 'Ordered_List', 'css': 'wym_tools_ordered_list'},
      {'name': 'InsertUnorderedList', 'title': 'Unordered_List', 'css': 'wym_tools_unordered_list'},
      {'name': 'Undo', 'title': 'Undo', 'css': 'wym_tools_undo'},
      {'name': 'Redo', 'title': 'Redo', 'css': 'wym_tools_redo'},
      {'name': 'CreateLink', 'title': 'Link', 'css': 'wym_tools_link'},
      {'name': 'Unlink', 'title': 'Unlink', 'css': 'wym_tools_unlink'},
      {'name': 'ToggleHtml', 'title': 'HTML', 'css': 'wym_tools_html'}
    ],
    updateSelector: 'input:submit',
    updateEvent: 'click',
    classesHtml: ''
  };

  // Initialize WYMeditors.
  $('textarea').filter(function() {
    // Skip the hidden template form.
    return (! this.id.match(/__prefix__/))
  }).wymeditor(wymconfig);

  // Initialize WYMeditors in new inline rows when they are added.
  $('body').bind('inlineadded', function(e, row) {
    // Need to rewrap the row in non-Django jQuery, which has wymeditor loaded.
    $(row[0]).find('textarea').wymeditor(wymconfig);
  });

  // Initialize timeago.
  $('time.timeago').timeago();
});
