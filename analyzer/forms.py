# analyzer/forms.py

from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()

class ShowAnswerForm(forms.Form):
    error_choices = forms.ChoiceField(widget=forms.RadioSelect)
