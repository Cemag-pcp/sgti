from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from urllib.parse import urlparse
from django.views.generic import ListView, View

from apps.core.mixins import SupervisorRequiredMixin, TechnicianRequiredMixin
from .models import CustomUser, RequesterProfile
from .forms import (
    CustomAuthenticationForm,
    CustomUserForm,
    RequesterForm,
    StyledPasswordResetForm,
    StyledSetPasswordForm,
)
from django.conf import settings


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url_allowed_hosts(self):
        # Avoid host validation failures on proxied deployments during the
        # post-login redirect step.
        return {
            'sgti.onrender.com',
            '.onrender.com',
            'localhost',
            '127.0.0.1',
            *self.success_url_allowed_hosts,
        }


class PasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/emails/password_reset_email.txt'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = StyledPasswordResetForm

    def get_extra_email_context(self):
        parsed_base_url = urlparse(settings.APP_BASE_URL)
        domain = parsed_base_url.netloc or self.request.get_host()
        protocol = parsed_base_url.scheme or ('https' if self.request.is_secure() else 'http')
        return {
            'domain': domain,
            'site_name': 'SGTI',
            'protocol': protocol,
        }


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = StyledSetPasswordForm


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _user_list_context(request, user_form=None, open_modal=False, edit_pk=None):
    return {
        'users': CustomUser.objects.filter(is_superuser=False).order_by('full_name'),
        'user_form': user_form or CustomUserForm(),
        'open_modal': open_modal,
        'edit_pk': edit_pk,
    }


def _requester_list_context(request, form=None, open_modal=False, edit_pk=None):
    qs = RequesterProfile.objects.order_by('full_name')
    search = request.GET.get('q', '')
    if search:
        qs = qs.filter(full_name__icontains=search) | qs.filter(matricula__icontains=search)
    return {
        'requesters': qs,
        'search': search,
        'requester_form': form or RequesterForm(),
        'open_modal': open_modal,
        'edit_pk': edit_pk,
    }


# ─── Usuários ─────────────────────────────────────────────────────────────────

class UserListView(SupervisorRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/user_list.html', _user_list_context(request))


class UserCreateView(SupervisorRequiredMixin, View):
    def post(self, request):
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso.')
            return redirect('accounts:user_list')
        return render(request, 'accounts/user_list.html',
                      _user_list_context(request, user_form=form, open_modal=True))


class UserUpdateView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado.')
            return redirect('accounts:user_list')
        return render(request, 'accounts/user_list.html',
                      _user_list_context(request, user_form=form, open_modal=True, edit_pk=pk))


class UserDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, 'Você não pode remover seu próprio usuário.')
            return redirect('accounts:user_list')
        user.delete()
        messages.success(request, 'Usuário removido.')
        return redirect('accounts:user_list')


# ─── Solicitantes ─────────────────────────────────────────────────────────────

class RequesterListView(TechnicianRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/requester_list.html', _requester_list_context(request))


class RequesterCreateView(SupervisorRequiredMixin, View):
    def post(self, request):
        form = RequesterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Solicitante cadastrado com sucesso.')
            return redirect('accounts:requester_list')
        return render(request, 'accounts/requester_list.html',
                      _requester_list_context(request, form=form, open_modal=True))


class RequesterUpdateView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        requester = get_object_or_404(RequesterProfile, pk=pk)
        form = RequesterForm(request.POST, instance=requester)
        if form.is_valid():
            form.save()
            messages.success(request, 'Solicitante atualizado.')
            return redirect('accounts:requester_list')
        return render(request, 'accounts/requester_list.html',
                      _requester_list_context(request, form=form, open_modal=True, edit_pk=pk))


class RequesterDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        requester = get_object_or_404(RequesterProfile, pk=pk)
        requester.delete()
        messages.success(request, 'Solicitante removido.')
        return redirect('accounts:requester_list')
