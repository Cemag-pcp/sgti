from django import forms
from .models import SoftwareRequest


class SoftwareRequestSubmitForm(forms.ModelForm):
    class Meta:
        model = SoftwareRequest
        fields = ['matricula', 'requester_name', 'setor', 'software_name', 'software_url', 'reason']
        widgets = {
            'matricula': forms.TextInput(attrs={'placeholder': 'Ex: 12345'}),
            'requester_name': forms.TextInput(attrs={'placeholder': 'Nome completo do responsável'}),
            'setor': forms.TextInput(attrs={'placeholder': 'Ex: Financeiro, RH, Produção...'}),
            'software_name': forms.TextInput(attrs={'placeholder': 'Ex: Monday, Slack, Notion...'}),
            'software_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
            'reason': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Descreva o motivo, processos beneficiados e quantos usuários usarão...',
            }),
        }


class TIAnalysisForm(forms.ModelForm):
    """Formulário preenchido pela TI durante a etapa de análise."""
    observation = forms.CharField(
        label='Observação',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Análise técnica, custos levantados, riscos identificados...',
        }),
    )

    class Meta:
        model = SoftwareRequest
        fields = ['needs_director_approval', 'estimated_cost', 'estimated_users']
        widgets = {
            'estimated_cost': forms.NumberInput(attrs={'placeholder': '0,00', 'step': '0.01'}),
            'estimated_users': forms.NumberInput(attrs={'placeholder': 'Nº de usuários'}),
        }
        labels = {
            'needs_director_approval': 'Requer aval da diretoria antes de prosseguir',
        }


class StageAdvanceForm(forms.Form):
    """Formulário genérico para avançar etapa com observação."""
    observation = forms.CharField(
        label='Observação',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Descreva o que foi feito ou decidido nesta etapa...',
        }),
    )


class RejectForm(forms.Form):
    """Formulário de reprovação."""
    observation = forms.CharField(
        label='Motivo da reprovação',
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Descreva o motivo pelo qual a solicitação está sendo reprovada...',
        }),
    )
