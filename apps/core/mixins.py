from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class TechnicianRequiredMixin(LoginRequiredMixin):
    """Permite acesso a Técnicos e Supervisores."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not hasattr(request.user, 'role') or request.user.role not in ('TECHNICIAN', 'SUPERVISOR'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SupervisorRequiredMixin(LoginRequiredMixin):
    """Permite acesso somente a Supervisores."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not hasattr(request.user, 'role') or request.user.role != 'SUPERVISOR':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
