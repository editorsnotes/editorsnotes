EditorsNotes.Views.Note = Backbone.View.extend({
  events: {
    'click .note-description': 'editDescription'
  },

  initialize: function (options) {
    var that = this
      , note = this.model

    this.sectionListView = new EditorsNotes.Views.NoteSectionList({ model: note });
    
    /*
    this.topicListView = new EditorsNotes.Views.RelatedTopicList({
      model: note,
      el: that.$('#note-related-topics');
    });
    */

    /*
    this.licenseChooser = new EditorsNotes.Views.NoteLicense({
      model: note,
      el: that.$();
    });
    */

  },

  render: function () {
    var that = this
      , template = EditorsNotes.Templates['note']

    this.$el.empty().html(template({ note: that.model.toJSON() }));
    this.sectionListView.setElement( that.$('#note-sections') );
    this.sectionListView.render()
    // this.topicListView.render();
  },

  editDescription: function () {
    var $description = this.$('#note-description')
      , html

    if ($description.hasClass('active')) return;

    $description.addClass('active').find('> div').editText({
      destroy: function (val) {
        note.set('content', val).save().done(function (resp) {
          $description.removeClass('active').html(resp.content);
        });
      }
    });
  },
  /*

    $('#note-description').on('click', function (e) {
      var $this = $(this)
        , $content = $('> div', $this)
        , html 

      if ($this.hasClass('active')) return;

      $this.addClass('active'); 
      $content.editText({
        destroy: function (val) {
          var promise = that.note.set('content', val).save();
          promise.then(function (resp) {
            $this.removeClass('active').html(resp.content)
          });
        }
      });

      html = ''
        + '<div class="row">'
          + '<a class="btn btn-primary save-changes pull-right">Save</a>'
        + '</div>'

      $(html).appendTo($this).on('click .btn', function (e) {
        setTimeout(function () { $content.editText('destroy') }, 0);
      });

    });

    */

});

EditorsNotes.Views['NoteSectionList'] = Backbone.View.extend({
  events: {
    'click .add-section': function (e) { 
      e.preventDefault();
      this.createSection( $(e.currentTarget).data('section-type') ); 
    }
  },

  initialize: function (options) {
    var that = this;

    this.note = this.model; // alias to make things more sensible

    this._sectionViews = [];
    this.activeRequests = [];

    this.listenTo(this.note.sections, 'add', this.addSection);
    this.listenTo(this.note.sections, 'remove', this.removeSection);
    this.listenTo(this.note.sections, 'sync', this.saveOrder);

    this.listenTo(this.note.sections, 'deactivate', this.deactivateSections);

    this.note.once('sync', function () {
      that.listenTo(that.note, 'request', that.showLoader);
      that.listenTo(that.note.sections, 'request', that.showLoader);
    });


  },

  render: function () {
    var template = EditorsNotes.Templates['note_section_list']

    $('body').addClass('editing');

    this._rendered = true;
    this.$el.empty().html( template() );

    // jQuery element lookups to save for later
    this.$loader = this.$('img.loader');
    this.$statusMessage = this.$('.status-message');
    this.$sections = this.$('.note-section-list');

    this._sectionViews.forEach(function (sectionView) {
      this.$sections.append(sectionView.el);
    }, this);


    this.initSort();
    this.initDrag();
  },

  showLoader: function (model, xhr) {
    var that = this
      , $msg = this.$statusMessage.hide()
      , $loader = this.$loader.show()

    this.activeRequests.push(xhr);

    xhr.always(function () {
      that.activeRequests.pop(xhr);
      if (!that.activeRequests.length) {
        $loader.hide();
        $msg.show()
          .css('opacity', 1)
          .animate({ 'opacity': 1 }, 700)
          .animate({ 'opacity': 0})
      }
    });
  },

  initSort: function () {
    var that = this;
    this.$sections.sortable({
      placeholder: 'section-placeholder',
      cancel: 'input,textarea,button,select,option,.note-section-edit-active',
      cursor: 'pointer',
      cursorAt: { 'left': 200, 'top': 20 },
      axis: 'y',
      tolerance: 'pointer',
      helper: function (event, item) {
        return $(item).clone().addClass('active').css({
          'max-height': '120px',
          'border': 'none',
          'opacity': .75
        });
      },
      start: function (event, ui) {
        that.deactivateSections();
        $(this).addClass('sort-active');
        ui.item.hide();
        that.$sections.sortable('refreshPositions');
      },
      stop: function (event, ui) {
        $(this).removeClass('sort-active');
        if (ui.item.hasClass('add-section')) {
          that.createSection(ui.item.data('section-type'), ui.item.index());
          ui.item.remove();
        }
      },
      update: function (event, ui) {
        if (ui.item.hasClass('add-section')) return;
        ui.item.show();
        that.saveOrder.call(that);
      }
    });
  },

  initDrag: function () {
    var that = this
      , $addBar = this.$('#citation-edit-bar').css('overflow', 'auto')
      , st

    $('.add-section', $addBar).draggable({
      axis: 'y',
      distance: 10,
      appendTo: $addBar,
      connectToSortable: that.$sections,
      helper: function (e, ui) {
        return $('<div class="drag-placeholder">')
          .html( $(this).html() )
          .css('width', that.$sections.innerWidth() - 22)
      },
      start: function (e, ui) {
        st = $(this).offsetParent().scrollTop();
      },
      drag: function (e, ui) {
        ui.position.top -= st;
      }
    });
  },

  createSection: function (sectionType, idx) {
    var _idx = idx || 0;

    // Sort is false because sections are ordered by the index of their ID in
    // the note's section_ordering field. Since this new section does not yet
    // have an ID, it can't be sorted.
    return this.note.sections.add(
      { 'section_type': sectionType }, 
      { at: _idx || 0, sort: false }
    ).at(_idx);
  },

  addSection: function (section) {
    var idx = section.collection.indexOf(section)
      , SectionView = EditorsNotes.Views['sections/' + section.get('section_type')]
      , view = new SectionView({ model: section })
      , target

    view.$el.data('sectionCID', view.model.cid);
    this._sectionViews.splice(idx, 0, view);

    if (!this._rendered) return;

    if (idx === 0) {
      this.$sections.prepend(view.el);
    } else {
      target = this.$sections.children()[idx - 1];
      view.$el.insertAfter(target);
    }

    if (section.isNew()) view.$el.trigger('click');
  },

  removeSection: function (section) {
    var that = this
      , sectionOrdering = this.note.get('section_ordering')
      , sectionViews = _(that._sectionViews)
      , viewToRemove

    viewToRemove = sectionViews.find(function (view) {
      return view.model === section
    });

    this._sectionViews = sectionViews.without(viewToRemove);

    sectionOrdering.pop(section.id);
    this.note.set('section_ordering', sectionOrdering);
  },

  deactivateSections: function (e) {
    var that = this;
    this._sectionViews.forEach(function (view) {
      view.deactivate.call(view);
    });
  },

  saveOrder: function () {
    var that = this
      , noteOrdering = this.note.get('section_ordering')
      , renderedOrder = []
      , viewOrdering = []
      , renderedOrder

    renderedOrder = this.$sections.children('.note-section').map(function (idx, el) {
      return $(el).data('sectionCID');
    }).toArray();

    this._sectionViews.sort(function (a, b) {
      var idxa = renderedOrder.indexOf(a.model.cid)
        , idxb = renderedOrder.indexOf(b.model.cid)

      return idxa > idxb;
    });

    this._sectionViews.forEach(function (view) {
      if (view.model.id) viewOrdering.push(view.model.id);
    });

    if (noteOrdering.join('') !== viewOrdering.join('')) {
      this.note.set('section_ordering', viewOrdering);
      this.note.save();
    }
  }

});

/*
 * Base view for all note sections. Children must define the following methods:
 *
 * `isEmpty`
 */

EditorsNotes.Views['NoteSection'] = Backbone.View.extend({
  tagName: 'div',
  className: 'note-section',
  isActive: false,

  events: { 'click': 'edit' },

  initialize: function () {
    this.render();
    this.$el.addClass('note-section-' + this.model.get('section_type'));
  },

  render: function () {
    var that = this
      , sectionType = this.model.get('section_type')
      , template = EditorsNotes.Templates['note_sections/' + sectionType]

    this.$el.html( template({ns: that.model.toJSON()}) );
    this.afterRender && this.afterRender.call(this);
  },

  edit: function () {
    var that = this
      , html

    if (this.isActive) return;

    this.model.collection.trigger('deactivate');

    this.isActive = true;
    this.$el.addClass('note-section-edit-active');
    this.$('.note-section-text-content').editText({
      initialValue: that.model.get('content'),
      destroy: function (val) {
        console.log('destroying');
        $(this).html(val);
        that.model.set('content', val);
        that.$('.edit-row').remove();
      }
    });

    html = ''
      + '<div class="edit-row row">'
        + '<a class="btn btn-primary save-section pull-right">Save</a>'
        + '<a class="btn btn-danger delete-section">Delete section</a>'
      + '</div>'

    $(html)
      .appendTo(this.$el)
      .on('click .btn', function (e) {
        var deleteSection = $(e.target).hasClass('delete-section');
        setTimeout(function () { that.deactivate.call(that, deleteSection); }, 10);
      });

    return;
  },

  deactivate: function (deleteModel) {
    var collection;

    if (!this.isActive) return;

    this.isActive = false;
    this.$el.removeClass('note-section-edit-active');

    if (this.isEmpty() || deleteModel) {
      collection = this.model.collection
      this.remove();
      this.model.destroy({
        success: function (model) {
          collection.remove(model);
          collection.trigger('removeEmpty');
        }
      });
    } else {
      this.$('.note-section-text-content').editText('destroy');
      this.model.save();
    }

    return;
  },
  
});

EditorsNotes.Views['sections/citation'] = EditorsNotes.Views.NoteSection.extend({
  afterRender: function () {
    var that = this
      , addDocumentView
      , $documentContainer

    if (!this.model.isNew()) return;

    selectDocumentView = new EditorsNotes.Views.SelectDocument({ project: this.model.project });
    $documentContainer = this.$('.citation-document').html(selectDocumentView.el);

    this.listenToOnce(selectDocumentView, 'documentSelected', function (doc) {
      $documentContainer.html(doc.get('description'));
      that.model.set('document_description', doc.get('description'));
      that.model.set('document', doc.url());
      selectDocumentView.remove();
    });

  },
  isEmpty: function () { return !this.model.has('document') }
});

EditorsNotes.Views['sections/note_reference'] = EditorsNotes.Views.NoteSection.extend({
  afterRender: function () {
    var that = this
      , addNoteView
      , $noteContainer

    if (!this.model.isNew()) return;

    addNoteView = new EditorsNotes.Views.SelectNote({ project: this.model.project });
    $noteContainer = this.$('.note-reference-note-container')
      .html(addNoteView.el);

    this.listenToOnce(addNoteView, 'noteSelected', function (note) {
      $noteContainer.html(note.get('title'));
      that.model.set('note_reference', note.url());
      that.model.set('note_reference_title', note.get('title'));
      addNoteView.remove();
    });
  },
  isEmpty: function () { return !this.model.has('note_reference') }
});

EditorsNotes.Views['sections/text'] = EditorsNotes.Views.NoteSection.extend({
  isEmpty: function () { return !this.model.get('content') }
});

/*
 * Base view for selecting items. Includes an autocomplete input and a button
 * to launch a modal for adding an item inline. Inheriting views must define
 * an `addItem` method to handle creating & rendering that modal.
 *
 * Options:
 *    project (required): slug of the project currently being worked on
 *    autocompleteopts: object defining settings for the autocomplete input
 */
EditorsNotes.Views['SelectItem'] = Backbone.View.extend({
  events: {
    'click .add-new-object': 'addItem'
  },
  initialize: function (options) {
    var that = this
      , url

    this.project = options.project;
    url = this.autocompleteURL.call(this)

    this._autocompleteopts = _.extend({
      select: that.selectItem.bind(that),
      appendTo: '#note-sections',
      minLength: 2,
      messages: {
        noResults: '',
        results: function () { return; }
      },
      source: function (request, response) {
        $.getJSON(url, {'q': request.term}, function (data) {
          response(data.results.map(function (item) {
            item.label = item[that.labelAttr || 'title'];
            return item;
          }));
        });
      },
    }, that.autocompleteopts || {})

    this.render();
  },
  render: function () {
    var that = this
      , $input

    this.$el.html(EditorsNotes.Templates.add_or_select_item({type: that.type}));

    $input = this.$('input');
    $input.autocomplete(that._autocompleteopts)
      .data('ui-autocomplete')._renderItem = function (ul, item) {
        return $('<li>')
          .data('ui-autocomplete-item', item)
          .append('<a>' + item.label + '</a>')
          .appendTo(ul)
      }
  }
});

EditorsNotes.Views['SelectDocument'] =  EditorsNotes.Views.SelectItem.extend({
  type: 'document',
  labelAttr: 'description',
  autocompleteURL: function () { return this.project.url() + 'documents/' },

  selectItem: function (event, ui) {
    this.trigger('documentSelected', this.project.documents.add(ui.item).get(ui.item.id));
  },

  addItem: function (e) {
    var that = this
      , addView = new EditorsNotes.Views.AddDocument({ project: this.project });

    e.preventDefault();

    this.listenTo(addView.model, 'sync', function (item) {
      that.trigger('documentSelected', item);
    });
    addView.$el.appendTo('body').modal();
  }
});

EditorsNotes.Views['SelectNote'] = EditorsNotes.Views.SelectItem.extend({
  type: 'note',
  labelAttr: 'title',
  autocompleteURL: function () { return this.project.url() + 'notes/'; },

  selectItem: function (event, ui) {
    this.trigger('noteSelected', this.project.notes.add(ui.item).get(ui.item.id));
  },

  addItem: function (e) {
    var that = this
      , addView = new EditorsNotes.Views.AddNote({ project: this.project });

    e.preventDefault();

    this.listenTo(addView.model, 'sync', function (item) {
      that.trigger('noteSelected', item);
    });
    addView.$el.appendTo('body').modal();
  }
});


/*
 * Base view for all views adding items in a modal
 *
 * Must create saveItem method
 *
 * options:
 *    height
 *    minHeight
 *    width
 */
EditorsNotes.Views['AddItem'] = Backbone.View.extend({
  renderModal: function () {
    var that = this
      , widget
      , $loader

    widget = EditorsNotes.Templates.add_item_modal({
      type: that.itemType,
      textarea: !!that.textarea
    });

    this.$el.html(widget).addClass('modal');
    $loader = this.$('.loader-icon');

    this.$el
      .on('ajaxStart', function () { $loader.show(); })
      .on('ajaxStop', function () { $loader.hide(); })
      .on('hidden', that.remove.bind(that))
      .on('shown', that.setModalSize.bind(that))
      .on('click', '.btn-save-item', that.saveItem.bind(that));
  },

  setModalSize: function () {
    var that = this
      , $w = $(window)
      , modalHeight
      , bodyHeight
      , modalPosition = {
        'my': 'top+20',
        'at': 'top',
        'of': $w,
        'collision': 'none',
      }

    modalHeight = this.options.height || (function () {
      var windowHeight = $w.height() - 50
        , minHeight = that.options.minHeight || 500

      return windowHeight > minHeight ? windowHeight : minHeight;
    })();

    bodyHeight = modalHeight
      - this.$('.modal-header').innerHeight()
      - this.$('.modal-footer').innerHeight()
      - (function (b) {
          var ptop = parseInt(b.css('padding-top'))
            , pbot = parseInt(b.css('padding-bottom'));
          return ptop + pbot;
        })(this.$('.modal-body'))
      - 2; // border

    this.$el.css({
      position: 'absolute',
      width: this.options.width || 840,
      height: modalHeight
    }).position(modalPosition).position(modalPosition);

    this.$('.modal-body').css({
      'height': bodyHeight,
      'max-height': bodyHeight
    });

  }
});

EditorsNotes.Views['AddDocument'] = EditorsNotes.Views.AddItem.extend({
  itemType: 'document',
  textarea: true,
  initialize: function (options) {
    this.model = options.project.documents.add({}, {at: 0}).at(0);
    this.render();
    this.$('.modal-body').append('<div class="add-document-zotero-data">');
    this.zotero_view = new EditorsNotes.Views.EditZoteroInformation({
      el: this.$('.add-document-zotero-data')
    });
  },

  render: function () {
    var that = this;

    this.renderModal();
    this.$el.on('hidden', function () {
      if (that.model.isNew()) that.model.destroy();
    });
  },

  saveItem: function (e) {
    var that = this
      , data = { description: this.$('.item-text-main').val() }
      , zotero_data = this.zotero_view.getZoteroData();

    e.preventDefault();

    if (!_.isEmpty(zotero_data)) {
      data.zotero_data = JSON.stringify(zotero_data);
    }

    this.model.set(data);
    this.model.save(data, {
      success: function () { that.$el.modal('hide') }
    });

  }
});

EditorsNotes.Views['AddNote'] = EditorsNotes.Views.AddItem.extend({
  itemType: 'note',
  initialize: function (options) {
    this.model = options.project.notes.add({}, {at: 0}).at(0);
    this.render();

    // TODO: assigned users & licensing
  },

  render: function () {
    var that = this;

    this.renderModal();

    this.$('.modal-body')
      .prepend('<h5>Title</h5>')
      .append(''
        + '<h5>Description</h5>'
        + '<textarea class="add-note-description" style="width: 98%; height: 80px;"></textarea>');
    this.$el.on('hidden', function () {
      if (that.model.isNew()) that.model.destroy();
    });
  },

  saveItem: function () {
    var that = this
      , data = {
        title: this.$('.item-text-main').val(),
        content: this.$('.add-note-description').val()
      }

    this.model.set(data);
    this.model.save(data, {
      success: function () { that.$el.modal('hide') }
    });
  }
});

EditorsNotes.Views['EditZoteroInformation'] = Backbone.View.extend({
  events: {
    'change .item-type-select': function (e) {
      this.renderZoteroForm(e.currentTarget.value);
    },
    'click .common-item-types li': function (e) {
      e.preventDefault();
      this.renderZoteroForm($('a', e.currentTarget).data('item-type'));
    },
    'click .add-creator': 'addCreator',
    'click .remove-creator': 'removeCreator',
    'input .zotero-entry': 'sendZoteroData',
  },

  initialize: function () {
    var that = this

    this.citeprocWorker = new Worker('/static/function/citeproc-worker.js');
    this.citeprocWorker.addEventListener('message', function (e) {
      that.$('.item-text-main').val(e.data.citation);
    });

    this.render();

    $.getJSON('/api/document/itemtypes/')
      .done(function (itemTypes) {
        var select = EditorsNotes.Templates['zotero/item_type_select'](itemTypes)

        that.$el.html('<hr />' + select);
        that.$('select').prop('selectedIndex', -1);
      })
      .error(function () {
        console.error('Could not fetch item types from server.');
      });
  },

  renderZoteroForm: function (itemType) {
    var that = this
      , $input = this.$('input').hide()

    $.get('/api/document/template/?itemType=' + itemType)
      .done(function (template) {
        var $template = $(template).filter('#zotero-information-edit');

        that.$el
          .html('<hr />' + $template.html())
          .find('.zotero-entry-delete').remove();
      })
      .fail(function () {
        alert('Could not retrieve template');
        $input.show()
      });
  },

  addCreator: function (e) {
    e.preventDefault();
    $(e.currentTarget).closest('.zotero-creator')
      .clone()
      .insertAfter($creator)
      .find('textarea').val('');
  },

  removeCreator: function (e) {
    var $creator = $(e.currentTarget).closest('.zotero-creator')

    e.preventDefault();
    $creator.siblings('.zotero-creator').length ?
      $creator.remove() :
      $('textarea', $creator).val('')
  },

  sendZoteroData: function () {
    this.citeprocWorker.postMessage({
      zotero_data: EditorsNotes.zotero.zoteroFormToObject(this.$el)
    });
  },
});
