$(document).ready(function () {
  var project = new EditorsNotes.Models.Project()
    , noteID = document.location.pathname.match(/notes\/(\d+)\//)[1]
    , note = project.notes.add({ id: noteID }).get(noteID)
    , view

  view = new EditorsNotes.Views.NoteSectionList({
    el: '#note-sections-container',
    model: note
  });

});
