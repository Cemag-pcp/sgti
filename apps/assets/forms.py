from django import forms

from .models import Asset


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'asset_tag', 'asset_type', 'brand', 'model', 'serial_number',
            'os', 'status', 'location', 'purchase_date', 'purchase_cost', 'warranty_until', 'notes',
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'warranty_until': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class AssetAssignForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['assigned_to_requester', 'assigned_to_staff']

    def clean(self):
        data = super().clean()
        if data.get('assigned_to_requester') and data.get('assigned_to_staff'):
            raise forms.ValidationError(
                'Selecione apenas um responsavel: colaborador OU equipe TI.'
            )
        return data


class AssetMaintenanceForm(forms.Form):
    notes = forms.CharField(
        label='Detalhes da manutencao',
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True,
        max_length=2000,
    )
