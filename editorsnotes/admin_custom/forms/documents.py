# -*- coding: utf-8 -*-

from django import forms
from django.forms.models import ModelForm, inlineformset_factory

from editorsnotes.djotero.widgets import ZoteroWidget
from editorsnotes.djotero.models import ZoteroLink
from editorsnotes.main.models.documents import (
    Document, DocumentLink, Scan, Transcript, Footnote)

from ..fields import MultipleFileInput

class DocumentForm(ModelForm):
    zotero_string = forms.CharField(required=False, widget=ZoteroWidget())
    class Media:
        js = (
            "function/admin-bootstrap-document.js",
        )
    class Meta:
        model = Document
        fields = ('description', 'edtf_date',)
        widgets = {
            'edtf_date': forms.widgets.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)

        if kwargs.has_key('instance'):
            document = kwargs['instance']
            self.initial['zotero_string'] = (
                document.zotero_link().zotero_data
                if document.zotero_link() else '')

    def save_zotero_data(self):
        document = self.instance
        if self.data.get('zotero-data-DELETE', '') == 'DELETE':
            if document.zotero_link():
                z = document.zotero_link()
                z.delete()
        if self.changed_data is not None and 'zotero_string' in self.changed_data:
            if document.zotero_link():
                z = document.zotero_link()
                z.zotero_data = self.cleaned_data['zotero_string']
                z.save()
            else:
                z = ZoteroLink.objects.create(
                    doc=document, zotero_data=self.cleaned_data['zotero_string'])
            return z
        else:
            return None

class DocumentLinkForm(ModelForm):
    class Meta:
        model = DocumentLink
        exclude = ('affiliated_projects',)
        widgets = {
            'description': forms.widgets.Textarea(
                attrs={ 'cols': 80, 'rows': 2 })
        }
DocumentLinkFormset = inlineformset_factory(
    Document, DocumentLink, form=DocumentLinkForm, extra=1)

class ScanForm(ModelForm):
    class Meta:
        fields = ('image', 'ordering')
        model = Scan
        widgets = {
            'image': MultipleFileInput(),
            'ordering': forms.HiddenInput()
        }

class ScanFormset(forms.models.BaseInlineFormSet):
    """
    If multiple images were posted from a single file input with the attribute
    "multiple", this formset will split them up into regular forms
    """
    def _construct_forms(self):
        self.forms = []
        forms_from_multiple_input = []

        for i in xrange(self.total_form_count()):
            form = self._construct_form(i)

            # Only pay attention to multiple files from an input if this is the
            # last image field and there is something to save
            if (i < self.total_form_count() - 1 or not form.files):
                self.forms.append(form)
                continue

            # If only one image was posted from this input, treat it as a normal
            # one. This allows us to treat this formset as it normally would be,
            # which is beneficial for several reasons, including continued
            # support for browsers that don't support the "multiple" attribute.
            images = form.files.getlist('%s-image' % form.prefix) 
            if len(images) == 1:
                self.forms.append(form)
                continue

            # Make a copy of the file & data dictionaries, which will be amended
            # in order to make new ScanForm instances
            newfiles = dict((k, v) for k, v in form.files.items())
            newdata = dict((k, v) for k, v in form.data.items())

            # Pretend that each image was posted individually
            j = i
            for image in images:
                prefix = self.add_prefix(j)
                newfiles['%s-image' % prefix] = image
                newdata['%s-ordering' % prefix] = j
                newform = self._construct_form(j, files=newfiles, data=newdata)
                forms_from_multiple_input.append(newform)
                j += 1

        # Only add these new forms to the formset if the images are valid. This
        # does go against the normal flow of validation, but it makes the
        # workflow for adding scans *much* less complicated to take an
        # all-or-nothing approach to accepting multiple images.
        if all(map(lambda f: f.is_valid(), forms_from_multiple_input)):
            self.forms += forms_from_multiple_input
        else:
            # Make the last form an empty one, like it was previously
            self.forms.append(
                self._construct_form(self.total_form_count() - 1, files=None))
            self.bad_multi_images = 'One or more files uploaded were not valid images.'

        # Does the management form need to be changed at all? I can't think of
        # any situation where it would be, but here's how it probably would be
        # done if needed.
        # self.management_form['initial']['TOTAL_FORMS'] = len(self.forms)
            
    # Display errors from a multiple upload field as a non-form error-- in the
    # formset, not the individual form
    def clean(self):
        if hasattr(self, 'bad_multi_images'):
            raise forms.ValidationError(self.bad_multi_images)

ScanFormset = inlineformset_factory(
    Document, Scan,
    form=ScanForm, formset=ScanFormset, extra=1)

class TranscriptForm(ModelForm):
    class Media:
        js = (
            'function/admin-bootstrap-transcript.js',
        )
    class Meta:
        model = Transcript
        fields = ('content',)

class FootnoteForm(ModelForm):
    class Meta:
        model = Footnote
        fields = ('content',)
    stamp = forms.CharField(required=False, widget=forms.HiddenInput)

FootnoteFormset = inlineformset_factory(
    Transcript, Footnote, form=FootnoteForm, extra=1)


