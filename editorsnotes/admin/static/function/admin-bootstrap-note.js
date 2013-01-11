$(document).ready(function() {
  /*
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
  $('.description-field .xhtml-textarea').wymeditor(wymconfig);
  */

  var editor = new wysihtml5.Editor('id_content', {
    toolbar: 'content-toolbar',
    parserRules: wysihtml5ParserRules,
    stylesheets: ['/static/function/wysihtml5/stylesheet.css']
  });

  editor.on('focus:composer', function() {
    var ed = this;
    setTimeout(function() {
      if (ed.textareaElement.value === '' &&
          ed.composer.selection.getSelectedNode() === ed.composer.element) {
        ed.composer.commands.exec('formatBlock', 'p');
      }
    });
  });

});
