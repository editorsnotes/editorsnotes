from models import *
from fields import XHTMLField, ReadonlyXHTMLWidget
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.fields import FieldDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import force_unicode
from django.utils.html import escape
from reversion import admin as reversion_admin
from urlparse import urlparse, parse_qsl, urlunparse
from urllib import urlencode
from pybtex.database.input import bibtex
from io import StringIO
from utils import xhtml_to_text
from fields import XHTMLField

class FootnoteAdminForm(forms.ModelForm):
    stamp = forms.CharField(required=False, widget=forms.HiddenInput)
    class Meta:
        model = Footnote

class DocumentAdminForm(forms.ModelForm):
    class Meta:
        model = Document
    def clean_description(self):
        value = self.cleaned_data['description']
        field = XHTMLField()
        if len(re.sub(r'[^\w\s]', '', 
                      xhtml_to_text(field.to_python(value)))) == 0:
            raise ValidationError('This field is required.')
        return value
    def clean_bibtex(self):
        parser = bibtex.Parser()
        value = self.cleaned_data['bibtex'].strip()
        if len(value) > 0: # empty value is OK
            data = parser.parse_stream(StringIO(value))
            if len(data.entries) == 0:
                raise ValidationError(
                    'This does not appear to be valid BibTex data.')
        return value
        

################################################################################

class CitationInline(generic.GenericStackedInline):
    model = Citation
    extra = 0
    template = 'admin/main/edit_inline/stacked.html'
    formfield_overrides = { 
        models.ForeignKey: { 
            'widget': forms.widgets.HiddenInput(
                attrs={ 'class': 'autocomplete-documents' }) } }

class TopicAssignmentInline(generic.GenericStackedInline):
    model = TopicAssignment
    extra = 1
    template = 'admin/main/edit_inline/stacked.html'
    formfield_overrides = { 
        models.ForeignKey: { 
            'widget': forms.widgets.HiddenInput(
                attrs={ 'class': 'autocomplete-topics' })}}

class AliasInline(admin.StackedInline):
    model = Alias
    extra = 0

class FootnoteInline(admin.StackedInline):
    model = Footnote
    extra = 0
    template = 'admin/main/footnote/edit_inline/stacked.html'
    form = FootnoteAdminForm
    formfield_overrides = { XHTMLField: { 'widget': ReadonlyXHTMLWidget } }

class DocumentLinkInline(admin.StackedInline):
    model = DocumentLink
    extra = 0

class ScanInline(admin.StackedInline):
    model = Scan

class UserProfileInline(admin.StackedInline):
    model = UserProfile

################################################################################

class VersionAdmin(reversion_admin.VersionAdmin):
    list_display = ('as_text', 'last_updater', 'last_updated')
    def save_model(self, request, obj, form, change):
        if not change: # adding new object
            obj.creator = request.user
        obj.last_updater = request.user
        obj.save()
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            try:
                instance.creator
            except ObjectDoesNotExist:
                instance.creator = request.user
            if 'last_updated' in instance._meta.get_all_field_names():
                instance.last_updater = request.user
            instance.save()
        formset.save_m2m()
    def response_add(self, request, obj, post_url_continue='../%s/'):
        if request.POST.has_key('_popup'):
            return HttpResponse('''<script type="text/javascript">
opener.$('body').trigger('addedviapopup', [ window, '%(pk)s', '%(obj)s' ]);
opener.dismissAddAnotherPopup(window, '%(pk)s', '%(obj)s');
</script>''' % { 'pk': escape(obj._get_pk_val()),
                 'obj': escape(obj) })
        response = super(VersionAdmin, self).response_add(request, obj, post_url_continue)
        if (request.POST.has_key('_continue') or 
            request.POST.has_key('_addanother')):
            return response
        return HttpResponseRedirect(obj.get_absolute_url())
    def response_change(self, request, obj):
        response = super(VersionAdmin, self).response_change(request, obj)
        if request.POST.has_key('_return_to') and not (
            request.POST.has_key('_continue') or 
            request.POST.has_key('_saveasnew') or 
            request.POST.has_key('_addanother')):
            return HttpResponseRedirect(request.POST['_return_to'])
        elif (request.POST.has_key('_return_to') and
              request.POST.has_key('_continue')):
            parts = list(urlparse(response['Location']))
            query = parse_qsl(parts[4])
            query.append(('return_to', request.POST['_return_to']))
            parts[4] = urlencode(query)
            response['Location'] = urlunparse(parts)
            return response
        else:
            return response
    def message_user(self, request, message):
        if 'success' in message.lower(): 
            messages.success(request, message)
        else:
            messages.info(request, message)

class ManyToManyAutocompleteWidget(forms.widgets.HiddenInput):
    def render(self, name, value, attrs=None):
        if value:
            value = ','.join([str(v) for v in value])
        else:
            value = ''
        return super(ManyToManyAutocompleteWidget, self).render(name, value, attrs)
    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        if value and ',' in value:
            return data[name].split(',')
        if value:
            return [value]
        return None
    def _has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        if len(initial) != len(data):
            return True
        for pk1, pk2 in zip(initial, data):
            if force_unicode(pk1) != force_unicode(pk2):
                return True
        return False

class TopicAdmin(VersionAdmin):
    inlines = (AliasInline, CitationInline)
    formfield_overrides = { 
        models.ManyToManyField: { 
            'widget': ManyToManyAutocompleteWidget(
                attrs={ 'class': 'autocomplete-multiple-topics vManyToManyRawIdAdminField' }) } }
    class Media:
        css = { 'all': ('style/custom-theme/jquery-ui-1.8.10.custom.css',
                        'style/admin.css') }
        js = ('function/jquery-1.5.1.min.js',
              'function/jquery-ui-1.8.10.custom.min.js',
              'function/wymeditor/jquery.wymeditor.pack.js',
              'function/jquery.timeago.js',
              'function/admin.js')

class NoteAdmin(VersionAdmin):
    inlines = (CitationInline, TopicAssignmentInline)
    class Media:
        css = { 'all': ('style/custom-theme/jquery-ui-1.8.10.custom.css',
                        'style/admin.css') }
        js = ('function/jquery-1.5.1.min.js',
              'function/jquery-ui-1.8.10.custom.min.js',
              'function/wymeditor/jquery.wymeditor.pack.js',
              'function/jquery.timeago.js',
              'function/admin.js')

class DocumentAdmin(VersionAdmin):
    form = DocumentAdminForm
    inlines = (TopicAssignmentInline, DocumentLinkInline, ScanInline)
    formfield_overrides = { 
        models.ForeignKey: { 
            'widget': forms.widgets.HiddenInput(
                attrs={ 'class': 'autocomplete-documents' }) } }
    class Media:
        css = { 'all': ('style/custom-theme/jquery-ui-1.8.10.custom.css',
                        'style/admin.css') }
        js = ('function/jquery-1.5.1.min.js',
              'function/jquery-ui-1.8.10.custom.min.js',
              'function/wymeditor/jquery.wymeditor.pack.js',
              'function/jquery.timeago.js',
              'function/admin.js')

class TranscriptAdmin(VersionAdmin):
    inlines = (FootnoteInline,)
    formfield_overrides = { 
        models.OneToOneField: { 
            'widget': forms.widgets.HiddenInput(
                attrs={ 'class': 'autocomplete-documents' }) } }
    def save_formset(self, request, form, formset, change):
        transcript = form.instance
        # Update the transcript HTML to remove any links to deleted footnotes.
        for footnote_form in formset.forms:
            if formset._should_delete_form(footnote_form):
                footnote_form.instance.remove_self_from(transcript)
        # Save the transcript formset.
        super(TranscriptAdmin, self).save_formset(request, form, formset, change)
        # Update the transcript HTML with correct links to any new footnotes.
        for footnote_form in formset.forms:
            if (hasattr(footnote_form, 'cleaned_data') and 
                'stamp' in footnote_form.cleaned_data):
                stamp = footnote_form.cleaned_data['stamp']
                if stamp:
                    a = transcript.content.cssselect('a.footnote[href="' + stamp + '"]')[0]
                    a.attrib['href'] = footnote_form.instance.get_absolute_url()
        # Save the transcript HTML.
        transcript.save()
    class Media:
        css = { 'all': ('style/custom-theme/jquery-ui-1.8.10.custom.css',
                        'style/admin.css',
                        'style/admin-transcript.css') }
        js = ('function/jquery-1.5.1.min.js',
              'function/jquery-ui-1.8.10.custom.min.js',
              'function/wymeditor/jquery.wymeditor.pack.js',
              'function/jquery.timeago.js',
              'function/jquery.ellipsis.js',
              'function/admin-transcript.js')

class FootnoteAdmin(VersionAdmin):
    formfield_overrides = { 
        models.ForeignKey: { 
            'widget': forms.widgets.HiddenInput(
                attrs={ 'class': 'autocomplete-transcripts' })}}
    class Media:
        css = { 'all': ('style/custom-theme/jquery-ui-1.8.10.custom.css',
                        'style/admin.css') }
        js = ('function/jquery-1.5.1.min.js',
              'function/jquery-ui-1.8.10.custom.min.js',
              'function/wymeditor/jquery.wymeditor.pack.js',
              'function/jquery.timeago.js',
              'function/admin.js')

class UserProfileAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'affiliation')
    def affiliation(self, user):
        try:
            return user.get_profile().affiliation or ''
        except UserProfile.DoesNotExist:
            return ''

admin.site.unregister(User)

admin.site.register(Topic, TopicAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Transcript, TranscriptAdmin)
admin.site.register(Footnote, FootnoteAdmin)
admin.site.register(Project)
admin.site.register(User, UserProfileAdmin)
