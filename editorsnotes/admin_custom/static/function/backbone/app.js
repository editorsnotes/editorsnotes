EditorsNotes.Views = {}
EditorsNotes.Models = {}
EditorsNotes.Templates = {}

EditorsNotes.wysihtml5BaseOpts = {
  parserRules: wysihtml5ParserRules,
  stylesheets: ['/static/function/wysihtml5/stylesheet.css'],
  useLineBreaks: false
}

// Change backbone sync so that we include the CSRF token before each request.
//
// TODO: only include it with write operations
var oldSync = Backbone.sync;
Backbone.sync = function (method, model, options) {
  options.beforeSend = function (xhr) {
    var token = $('input[name="csrfmiddlewaretoken"]').val()

    if (!token) {
      console.error('No CSRF token found.');
      return;
    }

    xhr.setRequestHeader('X-CSRFToken', token);
  }
  return oldSync(method, model, options);
};

(function () {
  var defaults = {
    toolbarType: 'full',
    className: '',
    minHeight: 200,
    idPrefix: 'texteditor_id_auto',
    container: '',
    initialValue: null,
    destroy: null
  }

  function Editor( $el, opts ) {
    var that = this;

    this.options = _.extend({}, defaults, opts);

    this.$el = $el;
    this.isTextarea = this.$el.is('textarea');

    this.$container = this.options.container ?
      this.$el.closest( this.options.container ) :
      this.$el.parent()

    this.id = (this.isTextarea && this.$el.attr('id')) ||
      _.uniqueId(that.options.idPrefix);

    this.$toolbar = $(EditorsNotes.Templates['wysihtml5_toolbar']({
      id: that.id + '-toolbar',
      type: that.options.toolbarType
    }));

    this.height = (function (h) {
      return h < that.options.minHeight ? that.options.minHeight : h;
    })(this.$el.innerHeight());

    this.init();
  }

  Editor.prototype.init = function () {
    var that = this
      , content = this.options.initialValue

    if (!content) {
     content = this.isTextarea ? this.$el.val() : this.$el.html();
    }

    this.$textarea = this.isTextarea ?
      $el :
      $('<textarea>').appendTo(this.$container)

    this.$container.css('min-height', that.height + 8);

    this.$textarea
      .attr('id', that.id)
      .css({
        opacity: 0,
        height: that.height,
        width: '99%'
      })
      .val(content)

    if (!this.isTextarea) this.$el.hide();

    this.$toolbar.insertBefore(that.$textarea);
    this.editor = new wysihtml5.Editor(that.id, _.extend({
      toolbar: that.$toolbar.attr('id')
    }, EditorsNotes.wysihtml5BaseOpts));

    this.editor.on('load', function () {
      that.$container.css('min-height', '')
    });

    return this.$el;
  }

  Editor.prototype.destroy = function () {
    var that = this
      , finalVal = this.editor.getValue()
      , toRemove = [
        'iframe.wysihtml5-sandbox',
        'input[name="_wysihtml5_mode"]',
      ]

    this.$container.find(toRemove.join(',')).remove();

    if (this.isTextarea) {
      this.$el.val(finalVal);
    } else {
      this.$textarea.remove();
    }

    this.$toolbar.remove();

    if ( typeof(this.options.destroy) === 'function' ) {
      this.options.destroy.call( that.$el, finalVal );
    }

    this.$el
      .show()
      .removeData('editor')
      .trigger('editor:destroyed', finalVal); 

  }

  Editor.prototype.value = function (val) {
    if (!val) {
      return this.editor.getValue()
    } else {
      this.editor.setValue(val);
    }
  }

  $.fn.editText = function (method) {
    var editor = this.data('editor');

    if (this.length !== 1) $.error('One at a time :(');

    if ( typeof(method) === 'object' || !method  ) {
      if (editor) return this;
      return this.data('editor', new Editor(this, method || {}));
    } else if ( !editor ) {
      $.error('Must initialize editor first.');
    } else if ( Editor.prototype[method] ) {
      return editor[method].apply(editor, Array.prototype.slice.call(arguments, 1));
    } else {
      $.error('No such method: ' + method);
    }
  }

})();
