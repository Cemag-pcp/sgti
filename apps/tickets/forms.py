from django import forms
from .models import Ticket, TimeEntry, TicketObservation, SLAConfig, Location, Device


class TicketSubmitForm(forms.ModelForm):
    matricula = forms.CharField(
        label='Matrícula',
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 12345'}),
    )
    requester_name = forms.CharField(
        label='Nome completo',
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Seu nome completo'}),
    )
    asset_tag = forms.CharField(
        label='Tombamento',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 001234'}),
    )

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'area', 'priority', 'location', 'device']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.filter(is_active=True)
        self.fields['location'].empty_label = 'Escolha o setor'
        self.fields['location'].required = True
        self.fields['device'].queryset = Device.objects.filter(is_active=True)
        self.fields['device'].empty_label = 'Escolha o dispositivo'
        self.fields['device'].required = True
        self.fields['area'].required = False
        field_order = ['matricula', 'requester_name', 'title', 'description', 'category', 'area', 'priority', 'location', 'device', 'asset_tag']
        self.order_fields(field_order)


class TicketEditForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'area', 'priority', 'location', 'device', 'due_date', 'asset']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.filter(is_active=True)
        self.fields['location'].empty_label = 'Selecione o setor (opcional)'
        self.fields['location'].required = False
        self.fields['device'].queryset = Device.objects.filter(is_active=True)
        self.fields['device'].empty_label = 'Selecione o dispositivo (opcional)'
        self.fields['device'].required = False


class TicketAssignForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['assigned_to']


class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status']


class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['started_at', 'ended_at', 'duration_minutes', 'notes']
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ended_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ObservationForm(forms.ModelForm):
    class Meta:
        model = TicketObservation
        fields = ['body', 'is_internal']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escreva sua observação...'}),
        }


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex: TI, RH, Financeiro'}),
            'description': forms.TextInput(attrs={'placeholder': 'Descrição opcional'}),
        }


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Impressora, Notebook, Desktop'}),
            'description': forms.TextInput(attrs={'placeholder': 'Descrição opcional'}),
        }


class SLAConfigForm(forms.ModelForm):
    class Meta:
        model = SLAConfig
        fields = ['resolution_hours', 'is_active']
        widgets = {
            'resolution_hours': forms.NumberInput(attrs={'min': 1, 'class': 'form-input w-32'}),
        }
        labels = {
            'resolution_hours': 'Prazo (horas)',
            'is_active': 'Ativo',
        }
