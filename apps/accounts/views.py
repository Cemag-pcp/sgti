import logging

from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, View

from apps.core.mixins import SupervisorRequiredMixin, TechnicianRequiredMixin
from .models import CustomUser, RequesterProfile
from .forms import CustomAuthenticationForm, CustomUserForm, RequesterForm

logger = logging.getLogger(__name__)


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

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception:
            logger.exception(
                'Login failed after authentication',
                extra={
                    'request_host': self.request.META.get('HTTP_HOST'),
                    'redirect_to': self.request.POST.get(self.redirect_field_name) or self.request.GET.get(self.redirect_field_name),
                    'user_email': getattr(form.get_user(), 'email', None),
                },
            )
            raise


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
