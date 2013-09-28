// As things stand now, items (documents, notes, topics) should be added
// within a project instance. This eases things in terms of dealing with
// URLs, although that could be changed in the future.
EditorsNotes.Models['Project'] = Backbone.Model.extend({
  initialize: function (attributes, options) {

    // If a slug was not explictly passed to the project instance, try to
    // derive it from the current URL
    var slug = (attributes && attributes.slug) || (function (pathname) {
      var match = pathname.match(/^\/(?:api\/)?projects\/([^\/]+)/)
      return match && match[1];
    })(document.location.pathname);

    // Throw an error if a slug could not be determined. Without that, we
    // can't determine the URL for documents/notes/topics.
    if (!slug) {
      throw new Error('Could not get project without url or argument');
    }
    this.set('slug', slug);

    // Instantiate the collections for documents, notes, and topics.
    this.documents = new EditorsNotes.Models.DocumentCollection([], { project: this });
    this.notes = new EditorsNotes.Models.NoteCollection([], { project: this });
    this.topics = new EditorsNotes.Models.TopicCollection([], { project: this });
  },

  url: function () { return '/api/projects/' + this.get('slug') + '/'; }
});


EditorsNotes.Models['Document'] = Backbone.Model.extend({
  initialize: function () {
    // As stated above, for now, we only work with documents inside an instance
    // of DocumentCollection inside a Project. This stuff should be part of a
    // base model, but I didn't do that because method inheritence in javascript
    // is icky. (so, TODO)
    this.project = (this.collection && this.collection.project);
    if (!this.project) {
      throw new Error('Add notes through a project instance');
    }
  },

  url: function () {
    // Make sure URLs end with slashes. This should also be part of a base
    // model. (TODO)
    var origURL = Backbone.Model.prototype.url.call(this);
    return origURL.slice(-1) === '/' ? origURL : origURL + '/';
  },

  defaults: {
    description: null,
    zotero_data: null,
    topics: []
  }
});

EditorsNotes.Models['DocumentCollection'] = Backbone.Collection.extend({
  model: EditorsNotes.Models.Document,

  initialize: function (models, options) {
    this.project = this.project || options.project;
  },

  url: function () { return this.project.url() + 'documents/'; }
});


var NoteSection = Backbone.Model.extend({
  idAttribute: 'section_id',

  initialize: function () {
    this.project = this.collection.project;
  },

  url: function () {
    return this.isNew() ?
      this.collection.url :
      this.collection.url + 's' + this.get('section_id') + '/';
  }
});

var NoteSectionList = Backbone.Collection.extend({
  model: NoteSection,

  initialize: function (models, options) {
    this.project = options.project;
  },

  parse: function (response) { return response.sections; }
});

EditorsNotes.Models['Note'] = Backbone.Model.extend({
  url: function() {
    // Same as EditorsNotes.Models.Document.url (ergo, same TODO as there)
    var origURL = Backbone.Model.prototype.url.call(this);
    return origURL.slice(-1) === '/' ? origURL : origURL + '/';
  },

  defaults: {
    'title': null,
    'content': null,
    'status': '1',
    'section_ordering': [],
    'topics': []
  },

  initialize: function (options) {
    var that = this;

    // Same as in EditorsNotes.Models.Document.initialize (TODO)
    this.project = (this.collection && this.collection.project);
    if (!this.project) {
      throw new Error('Add notes through a project instance');
    }

    // Add a collection of NoteSection items to this note
    this.sections = new NoteSectionList([], {
      url: that.url(),
      project: this.project
    });

    // Section ordering is a property of the Note, not the the individual
    // sections. So make them aware of that.
    this.sections.comparator = function (section) {
      var ordering = that.get('section_ordering');
      return ordering.indexOf(section.id);
    }
    this.topics = [];
  },

  parse: function (response) {
    var topicNames = response.topics.map(function (t) { return t.name });

    this.sections.set(response.sections);
    this.set('topics', topicNames);

    delete response.sections;
    delete response.topics;

    return response
  }
});

EditorsNotes.Models['NoteCollection'] = Backbone.Collection.extend({
  model: EditorsNotes.Models.Note,

  url: function () { return this.project.url() + 'notes/'; },

  initialize: function (models, options) {
    this.project = options.project;
  }
});


EditorsNotes.Models['Topic'] = Backbone.Model.extend({
  initialize: function () {
    this.project = this.collection && this.collection.project;
    if (!this.project) {
      throw new Error('Add notes through a project instance');
    }
  },

  defaults: {
    preferred_name: null,
    topic_node_id: null,
    type: null,
    summary: null
  },

  url: function () {
    return this.isNew() ?
      this.collection.url :
      this.colection.url + this.get('topic_node_id') + '/';
  }

});

EditorsNotes.Models['TopicCollection'] = Backbone.Collection.extend({
  model: EditorsNotes.Models.Topic,

  initialize: function (models, options) {
    this.project = this.project || options.project
  },

  url: function () { return this.project.url() + 'topics/'; }
});




