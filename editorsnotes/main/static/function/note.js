function backboneInit(e) {
  var project = new EditorsNotes.Models.Project()
    , noteID = document.location.pathname.match(/notes\/(\d+)\//)[1]
    , note = project.notes.add({ id: noteID }).get(noteID)
    , noteView = new EditorsNotes.Views.Note({
      model: note,
      el: '#note'
    });

    noteView.model.fetch()
      .done(function () { noteView.render(); })
      .fail(function () { alert('error') })

}

$(document).ready(function() {
  $('<button class="btn-large btn-danger">EDIT</button>')
    .appendTo('body')
    .css('position', 'fixed')
    .on('click', function(e) { backboneInit(e); $(this).remove(); })
    .position({ my: 'right-64', at: 'right', of: window })
});
