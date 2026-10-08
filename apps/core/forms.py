from django import forms

from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['name', 'app_type', 'billing_type', 'responsible', 'url', 'release_date', 'description', 'notes', 'is_active']
        widgets = {
            'release_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('app_type') != Application.EXTERNAL:
            cleaned_data['billing_type'] = ''
        return cleaned_data
