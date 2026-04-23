from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import CustomUser, RequesterProfile


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'seu@email.com',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '••••••••',
        }),
    )


class CustomUserForm(forms.ModelForm):
    password = forms.CharField(
        label='Senha',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        help_text='Deixe em branco para manter a senha atual (na edição).',
    )

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'role', 'is_active']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
        return user


class RequesterForm(forms.ModelForm):
    class Meta:
        model = RequesterProfile
        fields = ['matricula', 'full_name', 'email', 'phone', 'whatsapp_phone']
        widgets = {
            'matricula': forms.TextInput(attrs={'placeholder': 'Ex: 12345'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Nome completo'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@empresa.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'whatsapp_phone': forms.TextInput(attrs={'placeholder': '5511999999999'}),
        }


class StyledPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'seu@email.com',
            'autofocus': True,
        }),
    )


class StyledSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Digite a nova senha',
        }),
    )
    new_password2 = forms.CharField(
        label='Confirmar nova senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Repita a nova senha',
        }),
    )
