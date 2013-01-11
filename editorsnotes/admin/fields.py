from django import forms

class MultipleFileInput(forms.ClearableFileInput):
    def __init__(self, *args, **kwargs):
        self.template_with_initial = '%(initial)s'
        super(MultipleFileInput, self).__init__(*args, **kwargs)
    def render(self, name, value, attrs=None):
        attrs = attrs if attrs else {}
        if value is None:
            attrs['multiple'] = 'multiple'
        return super(MultipleFileInput, self).render(name, value, attrs=attrs)
