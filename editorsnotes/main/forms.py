from django import forms

PURPOSE_CHOICES = (
    ('1', 'Feedback'),
    ('2', 'Bug report'),
    ('3', 'Request for account'),
    ('9', 'Other')
)

class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=50, label='Your name')
    email = forms.EmailField(label='Your email')
    purpose = forms.ChoiceField(choices=PURPOSE_CHOICES)
    message = forms.CharField(widget=forms.Textarea(
        attrs={'cols': '50', 'rows': '7', 'style': 'width: 50em;' }))
