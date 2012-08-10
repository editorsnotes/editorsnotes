from django import forms
from models import ZoteroLink
from widgets import ZoteroWidget

class ZoteroForm(forms.Form):
    zotero_data = forms.CharField(
        widget=ZoteroWidget())
