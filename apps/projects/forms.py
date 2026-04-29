from django import forms
from django.contrib.auth import get_user_model

from .models import Project, ProjectMember, ProjectTask, ProjectUpdate

User = get_user_model()

_input = 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'
_select = _input
_textarea = _input + ' resize-none'


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'objective', 'area',
            'status', 'priority', 'responsible', 'start_date', 'end_date',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': _input, 'placeholder': 'Ex: Automação de atividades do Compras'}),
            'description': forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Descreva o projeto...'}),
            'objective': forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Qual o objetivo deste projeto?'}),
            'area': forms.Select(attrs={'class': _select}),
            'status': forms.Select(attrs={'class': _select}),
            'priority': forms.Select(attrs={'class': _select}),
            'responsible': forms.Select(attrs={'class': _select}),
            'start_date': forms.DateInput(attrs={'class': _input, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': _input, 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible'].queryset = User.objects.filter(
            role__in=('SUPERVISOR', 'TECHNICIAN')
        ).order_by('full_name')
        self.fields['responsible'].empty_label = '— Selecione —'
        self.fields['responsible'].required = True


    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'A previsao de termino nao pode ser anterior a data de inicio.')
        return cleaned_data


class ProjectTaskForm(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ['title', 'description', 'status', 'priority', 'assignee', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': _input, 'placeholder': 'Título da tarefa'}),
            'description': forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Descrição opcional...'}),
            'status': forms.Select(attrs={'class': _select}),
            'priority': forms.Select(attrs={'class': _select}),
            'assignee': forms.Select(attrs={'class': _select}),
            'due_date': forms.DateInput(attrs={'class': _input, 'type': 'date'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignee'].empty_label = '— Sem responsável —'
        self.fields['assignee'].required = False
        if project:
            member_ids = project.members.values_list('user_id', flat=True)
            qs = User.objects.filter(id__in=member_ids).order_by('full_name')
            if not qs.exists():
                qs = User.objects.filter(role__in=('SUPERVISOR', 'TECHNICIAN')).order_by('full_name')
            self.fields['assignee'].queryset = qs
        else:
            self.fields['assignee'].queryset = User.objects.filter(
                role__in=('SUPERVISOR', 'TECHNICIAN')
            ).order_by('full_name')


class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ['user', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': _select}),
            'role': forms.Select(attrs={'class': _select}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].label = 'Usuário'
        self.fields['role'].label = 'Papel'
        if project:
            existing = project.members.values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role__in=('SUPERVISOR', 'TECHNICIAN')
            ).exclude(id__in=existing).order_by('full_name')
        else:
            self.fields['user'].queryset = User.objects.filter(
                role__in=('SUPERVISOR', 'TECHNICIAN')
            ).order_by('full_name')


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = ProjectUpdate
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': _textarea,
                'rows': 3,
                'placeholder': 'Registre uma atualização, decisão ou progresso...',
            }),
        }
        labels = {'content': 'Nova atualização'}
