$(document).ready(function() {
  var editor = new wysihtml5.Editor('id_topicsummary-0-content', {
    toolbar: 'summary-toolbar',
    parserRules: wysihtml5ParserRules,
    stylesheets: ['/static/function/wysihtml5/stylesheet.css']
  });
});
