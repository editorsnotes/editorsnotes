$(document).ready(function(){
  var csrf_token = $("input[name='csrfmiddlewaretoken']").attr('value');
  
  // Set up selection for all lists
  $(".djotero-list.active li").live({
    mouseenter : function() {
      if ( $(this).hasClass('item-selected') == false ) {
        $(this).addClass('item-hover');
      }
    },
    mouseleave : function() {
      $(this).removeClass('item-hover');
    },
    click : function() {
      $(this).siblings().removeClass('item-selected');
      $(this).addClass('item-selected');
    }
  });
  
  $('.library-item').live('click', function() {
    $('.after-library').show();
  });
  
  // Get access list of Zotero libraries
  $('#get-libraries').click(function(){
    $(this).replaceWith('<img src="/media/style/icons/ajax-loader.gif">');
    $.getJSON('access', function(data) {
      $('#libraries img').remove();
      var i = 1
      $.each(data.libraries, function (key, value) {
        var library = $('<li>')
          .attr({
            'class' : 'library-item',
            'location' : value.location,
            'id' : 'library-' + i
          })
          .text(value.title);
        $('#library-list').append(library);
        i++
      });
    });
  });



  // Get list of collections in a library
  $('#get-collections').click(function(){
    $(this).replaceWith('<img src="/media/style/icons/ajax-loader.gif">');
    $('#library-list').removeClass('active');
    var base = $("#library-list .item-selected").attr('location');
    $.getJSON('collections', {'loc' : base }, function(data) {
      $('#collections img').remove();
      var i = 1
      $.each(data.collections, function (key, value) {
        var collection = $('<li>')
          .attr({
            'class' : 'collection-item',
            'location' : value.location,
            'id' : 'collection-' + i
          })
          .text(value.title);
        $('#collection-list').append(collection);
        i++
      });
    });
  });
  
  // Query last 10 items in selected library (or collection)
  $("#get-items").click(function(){
    $(this).replaceWith('<img src="/media/style/icons/ajax-loader.gif">');
    if( $('#collection-list').find('.item-selected').length > 0 ) {
      var selectedSource = $("#collection-list .item-selected").attr('location');
    }
    else {
      var selectedSource = $("#library-list .item-selected").attr('location');
    }
    $.getJSON('items', {'loc' : selectedSource }, function(data) {
      $('#access').hide();
      $('#items').show();
      var counter = 1
      $.each(data.items, function (key, value) {
      
        // Start citeproc processing
        var item_csl = eval( "(" + value.item_csl + ")" );
        var bibdata = {"ITEM-1" : item_csl}
        var citation_object = {"citationItems": [{"id" : "ITEM-1"}], "properties": {"noteIndex": 0}}
        var sys = {retrieveItem: function(id){return bibdata[id];}, retrieveLocale: function(lang){return locale[lang];}}
        
        citeproc = new CSL.Engine(sys, chicago_fullnote_bibliography2);
        citeproc.setOutputFormat("text");
        CSL.Output.Formats.text["@font-style/italic"] = "<i>%%STRING%%</i>"
        citeproc.appendCitationCluster( citation_object );
        var citation = citeproc.makeBibliography()[1];
        var parser = new CSL.DateParser;
        var date = parser.parse(value.date)
        // End citeproc processing
          
        var checkbox = $('<input>').attr({
          type: 'checkbox',
          name: 'item',
          value: '{ "json" : ' + value.item_json + ', "url" : \"' + value.url + '\", "date" : ' + JSON.stringify(date) + ', "csl" : \"' + citation + '\", "related_object" : \"' + "{{ related_object }}" + '\", "related_id" : \"' + "{{ related_id }}" + '\"}'
        });
        
        var input = $('<div class="zotero-link">').attr("id", "z" + counter).append('<a class="add-to-document"><img width="10" height="10" alt="Add Another" src="/django_admin_media/img/admin/icon_addlink.gif">&nbsp;').append(checkbox).append('<a class="zotero-object" href="' + value.url + '" target="_blank">' + value.title + '</a>');
        
        counter = counter + 1
        
        $('#item-list').append(input);
      
      });
      var submit = $('<input>').attr({type: 'submit', value: 'Import selected items'});
      $('#item-list').append(submit);
    });
  });
  
  $("#doc-add-form").dialog({
    autoOpen: false,
    modal: true,
    width: 500,
    title: 'Connect to existing document'
  });
  
  $('.add-to-document').live('click', function(){
    var link = $(this).parent()
    $('#document')
      .html(link.find('.zotero-object')[0].text)
      .attr('source', link.attr('id'))
      .attr('value', link.find('input').attr('value'));
    $("#doc-add-form").dialog('open');
  });
  
  $('#docsearch input')
    .autocomplete({
      source: function(request, response) {
        $.getJSON('/api/documents/', { q: request.term }, function(data) {
          response($.map(data, function(item, index) {
            return { label: item.description, id: item.id };
          }));
        });
      },
      minLength: 3,
      select: function(event, ui) {
        if (ui.item) {
          $('#link-document').show()
            .attr('document', ui.item.id);
        }
      }
  });
  $('#link-document').click(function(){
    $.post("update_link/", { 
        'doc_id' : $(this).attr('document'),
        'zotero_info' : $('#document').attr('value'),
        'csrfmiddlewaretoken': csrf_token
    },
        function(data) {
            var old_div = $('#document').attr('source');
            $('#' + old_div ).remove();
            $('#docsearch input')[0].value = "";
            $("#doc-add-form").dialog('close');
        }
    );
  });
});
