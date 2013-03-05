$(document).ready(function () {
  var $formset = $('#footnote-formset')
    , editor

  function addFootnote(stamp, anchoredText) {
    $formset
      .one('formsetAppended', function (e, newFootnote) {
        var $newFootnote = $(newFootnote);

        $('.footnote-anchor', $newFootnote)
          .text(anchoredText);

        $newFootnote
          .removeClass('hide')
          .editText();
      })
      .appendFormset('.footnote-edit', {stamp: stamp.slice(1)});
  }

  $formset
    .on('click', '.footnote-edit:not(.section-edit-active)', function (e) {
      $(this).editText();
    });

  wysihtml5.commands.footnote = {
    exec: function(composer, command, param) {
      var selection = composer.selection.getSelection()
        , selectedText = selection.toString()
        , overlap = false
        , stamp = _.uniqueId('#newfootnote')

      if (this.state(composer, command)) {
        // Focus selected footnote for editing, maybe?

      } else {
        // Create a new footnote, both as an anchor in the transcript text and
        // a new footnote form to save.

        if (!selectedText){
          alert('Select text to create a footnote.');
          return;
        } 

        // Check if selected text overlaps with other footnotes
        $(composer.element).find('.footnote').each(function () {
          if (selection.containsNode(this, true)) {
            overlap = true;
            return;
          }
        });

        if (overlap) {
          alert('Footnotes can not overlap.');
          return;
        }

        wysihtml5.commands.createLink.exec(composer, 'createLink', {
          'class': 'footnote',
          'href': window.location.pathname + stamp // stamp
        });

        addFootnote(stamp, selectedText);
      }
    },
    state: function(composer, command) {
      var selection = composer.selection.getSelection()
        , parentElement

      if (!selection) {
        return false;
      }
  
      parentElement = selection.focusNode.parentElement;
      return (parentElement
              && parentElement.nodeName.toUpperCase() === 'A'
              && parentElement.classList.contains('footnote'))

    },
    value: function() {
      return undefined;
    }
  }

  editor = new wysihtml5.Editor('id_content', {
    toolbar: 'content-toolbar',

    parserRules: (function (rules) {
      var transcriptRules = rules;
      transcriptRules.tags.a = {
        check_attributes: {'href': 'src'}
      }
      transcriptRules.classes['footnote'] = 1;
      return transcriptRules;
    })(wysihtml5ParserRules),

    stylesheets: ['/static/function/wysihtml5/stylesheet.css']
  });

  editor.on('load', function () {
    var footnotes = getFootnoteIds(editor);

    function arrDifference(arr, without) {
      var difference = [];

      for (var i = 0; i < arr.length; i++) {
        if (without.indexOf(arr[i]) === -1) {
          difference.push(arr[i])
        }
      }

      return difference;
    }


    function getFootnoteIds(editor) {
      var footnotes = editor.composer.element.querySelectorAll('a.footnote')
        , footnoteIds = []

      for (var i = 0; i < footnotes.length; i++) {
        if (footnotes[i].pathname) {
          footnoteIds.push(footnotes[i].pathname);
        }
      }

      return footnoteIds;
    }

    function getFootnoteNode(href) {
      var footnoteDOMid = /newfootnote/.test(href) ?
        href.match(/newfootnote\d+/)[0] :
        href.match(/\d+/)[0];
      return $('#footnote-' + footnoteDOMid);
    }

    $(editor.composer.element).on('keypress cut paste undo:composer redo:composer', function () {
      setTimeout(function () {
        var footnotesNow = getFootnoteIds(editor)
          , deletedFootnotes
          , undeletedFootnotes

        // Footnotes have been deleted
        if (footnotesNow.length < footnotes.length) {
          deletedFootnotes = arrDifference(footnotes, footnotesNow);
          deletedFootnotes.forEach(function (footnoteHref) {
            var $footnoteNode = getFootnoteNode(footnoteHref);
            if (!$footnoteNode.length) { 
              return;
            }
            $footnoteNode
              .css({'background': 'red'})
              .fadeOut('slow')
              .find(':input[name$="DELETE"]')
                .prop('checked', true);
          });
          footnotes = footnotesNow;

        // Footnotes have been restored
        } else if (footnotesNow.length > footnotes.length) {
          undeletedFootnotes = arrDifference(footnotesNow, footnotes);
          undeletedFootnotes.forEach(function (footnoteHref) {
            var $footnoteNode = getFootnoteNode(footnoteHref);
            if (!$footnoteNode.length) {
              return;
            }
            $footnoteNode
              .css('background', 'green')
              .fadeIn('slow', function () {
                $footnoteNode.css('background', 'none');
              })
              .find(':input[name$="DELETE"]')
                .prop('checked', false);
          });
          footnotes = footnotesNow;
        }

      }, 5);
    });

  });

});
