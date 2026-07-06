from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from apps.core.mixins import TechnicianRequiredMixin, SupervisorRequiredMixin
from .forms import ProjectForm, ProjectMemberForm, ProjectTaskForm, ProjectUpdateForm
from .models import Project, ProjectMember, ProjectTask, ProjectUpdate


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _kanban_columns(project):
    tasks_by_status = {key: [] for key, _ in ProjectTask.STATUS_CHOICES}
    for task in project.tasks.select_related('assignee').order_by('order', '-created_at'):
        tasks_by_status[task.status].append(task)
    return [(key, label, tasks_by_status[key]) for key, label in ProjectTask.STATUS_CHOICES]


def _render_kanban_board(request, project):
    return render_to_string(
        'projects/partials/kanban_board.html',
        {
            'project': project,
            'kanban_columns': _kanban_columns(project),
            'can_manage_project': project.can_manage(request.user),
        },
        request=request,
    )


def _render_members_panel(request, project):
    return render_to_string(
        'projects/partials/members_panel.html',
        {
            'project': project,
            'can_manage_project': project.can_manage(request.user),
        },
        request=request,
    )


def _render_updates_panel(request, project, update_form=None):
    return render_to_string(
        'projects/partials/updates_panel.html',
        {
            'project': project,
            'update_form': update_form or ProjectUpdateForm(),
            'is_supervisor': request.user.is_supervisor,
        },
        request=request,
    )


class ProjectListView(TechnicianRequiredMixin, View):
    def get(self, request):
        qs = (
            Project.objects.select_related('responsible', 'created_by')
            .prefetch_related('tasks', 'members')
        )
        if not request.user.is_supervisor:
            qs = qs.filter(
                Q(created_by=request.user)
                | Q(responsible=request.user)
                | Q(members__user=request.user)
            ).distinct()
        status = request.GET.get('status')
        priority = request.GET.get('priority')
        area = request.GET.get('area')
        q = request.GET.get('q', '').strip()
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if area:
            qs = qs.filter(area=area)
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(code__icontains=q)
                | Q(description__icontains=q)
            )

        counts = {
            'total': qs.count(),
            'planning': qs.filter(status=Project.PLANNING).count(),
            'in_progress': qs.filter(status=Project.IN_PROGRESS).count(),
            'completed': qs.filter(status=Project.COMPLETED).count(),
        }

        return render(request, 'projects/project_list.html', {
            'projects': qs,
            'counts': counts,
            'status_choices': Project.STATUS_CHOICES,
            'priority_choices': Project.PRIORITY_CHOICES,
            'area_choices': Project.AREA_CHOICES,
            'filters': request.GET,
        })


class ProjectCreateView(TechnicianRequiredMixin, View):
    def get(self, request):
        return render(request, 'projects/project_form.html', {
            'form': ProjectForm(),
            'title': 'Novo Projeto',
        })

    def post(self, request):
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            ProjectMember.objects.create(
                project=project,
                user=request.user,
                role=ProjectMember.MANAGER,
                added_by=request.user,
            )
            if project.responsible and project.responsible != request.user:
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=project.responsible,
                    defaults={'role': ProjectMember.MANAGER, 'added_by': request.user},
                )
            messages.success(request, f'Projeto {project.code} criado com sucesso.')
            return redirect('projects:detail', pk=project.pk)
        return render(request, 'projects/project_form.html', {
            'form': form,
            'title': 'Novo Projeto',
        })


class ProjectDetailView(TechnicianRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(
            Project.objects.select_related('responsible', 'created_by')
                           .prefetch_related('members__user', 'tasks__assignee', 'updates__author'),
            pk=pk,
        )
        if not project.can_view(request.user):
            raise PermissionDenied

        return render(request, 'projects/project_detail.html', {
            'project': project,
            'kanban_columns': _kanban_columns(project),
            'task_form': ProjectTaskForm(project=project),
            'member_form': ProjectMemberForm(project=project),
            'update_form': ProjectUpdateForm(),
            'is_supervisor': request.user.is_supervisor,
            'can_manage_project': project.can_manage(request.user),
        })


class ProjectUpdateView(TechnicianRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(Project.objects.prefetch_related('updates__author'), pk=pk)
        if not project.can_manage(request.user):
            messages.error(request, 'Sem permissão para editar este projeto.')
            return redirect('projects:detail', pk=pk)
        return render(request, 'projects/project_form.html', {
            'form': ProjectForm(instance=project),
            'project': project,
            'title': f'Editar — {project.name}',
        })

    def post(self, request, pk):
        project = get_object_or_404(Project.objects.prefetch_related('updates__author'), pk=pk)
        if not project.can_manage(request.user):
            messages.error(request, 'Sem permissão para editar este projeto.')
            return redirect('projects:detail', pk=pk)
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            if project.responsible:
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=project.responsible,
                    defaults={'role': ProjectMember.MANAGER, 'added_by': request.user},
                )
            messages.success(request, 'Projeto atualizado.')
            return redirect('projects:detail', pk=pk)
        return render(request, 'projects/project_form.html', {
            'form': form,
            'project': project,
            'title': f'Editar — {project.name}',
        })


class ProjectStatusUpdateView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_manage(request.user):
            raise PermissionDenied
        new_status = request.POST.get('status')
        if new_status in dict(Project.STATUS_CHOICES):
            project.status = new_status
            project.save()
            messages.success(request, f'Status do projeto atualizado para "{project.get_status_display()}".')
        else:
            messages.error(request, 'Status inválido.')
        return redirect('projects:detail', pk=pk)


class ProjectDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project.objects.prefetch_related('updates__author'), pk=pk)
        code = project.code
        project.delete()
        messages.success(request, f'Projeto {code} removido.')
        return redirect('projects:list')


class ProjectTaskCreateView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_manage(request.user):
            raise PermissionDenied
        form = ProjectTaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            if _is_ajax(request):
                return JsonResponse({'ok': True, 'board_html': _render_kanban_board(request, project)})
            messages.success(request, 'Tarefa criada.')
        else:
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
            messages.error(request, 'Erro ao criar tarefa.')
        return redirect('projects:detail', pk=pk)


class ProjectTaskUpdateView(TechnicianRequiredMixin, View):
    def post(self, request, pk, task_pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_manage(request.user):
            raise PermissionDenied
        task = get_object_or_404(ProjectTask, pk=task_pk, project=project)
        form = ProjectTaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            form.save()
            if _is_ajax(request):
                return JsonResponse({'ok': True, 'board_html': _render_kanban_board(request, project)})
            messages.success(request, 'Tarefa atualizada.')
        else:
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
            messages.error(request, 'Erro ao atualizar tarefa.')
        return redirect('projects:detail', pk=pk)


class ProjectTaskStatusView(TechnicianRequiredMixin, View):
    def post(self, request, pk, task_pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_manage(request.user):
            raise PermissionDenied
        task = get_object_or_404(ProjectTask, pk=task_pk, project=project)
        new_status = request.POST.get('status')
        if new_status in dict(ProjectTask.STATUS_CHOICES):
            task.status = new_status
            task.save(update_fields=['status', 'updated_at'])
            return JsonResponse({'ok': True, 'status': task.status, 'status_display': task.get_status_display()})
        return JsonResponse({'error': 'Status inválido'}, status=400)


class ProjectTaskDeleteView(TechnicianRequiredMixin, View):
    def post(self, request, pk, task_pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_manage(request.user):
            raise PermissionDenied
        task = get_object_or_404(ProjectTask, pk=task_pk, project=project)
        task.delete()
        if _is_ajax(request):
            return JsonResponse({'ok': True, 'board_html': _render_kanban_board(request, project)})
        messages.success(request, 'Tarefa removida.')
        return redirect('projects:detail', pk=pk)


class ProjectMemberAddView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_manage(request.user):
            raise PermissionDenied
        form = ProjectMemberForm(request.POST, project=project)
        if form.is_valid():
            member = form.save(commit=False)
            member.project = project
            member.added_by = request.user
            member.save()
            if _is_ajax(request):
                return JsonResponse({'ok': True, 'panel_html': _render_members_panel(request, project)})
            messages.success(request, f'{member.user.full_name} adicionado ao projeto.')
        else:
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
            messages.error(request, 'Erro ao adicionar membro.')
        return redirect('projects:detail', pk=pk)


class ProjectMemberRemoveView(TechnicianRequiredMixin, View):
    def post(self, request, pk, member_pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_manage(request.user):
            raise PermissionDenied
        member = get_object_or_404(ProjectMember, pk=member_pk, project=project)
        if member.user_id in {project.created_by_id, project.responsible_id}:
            error = 'Nao e permitido remover o criador ou o responsavel do projeto.'
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'error': error}, status=400)
            messages.error(request, error)
            return redirect('projects:detail', pk=pk)
        name = member.user.full_name
        member.delete()
        if _is_ajax(request):
            return JsonResponse({'ok': True, 'panel_html': _render_members_panel(request, project)})
        messages.success(request, f'{name} removido do projeto.')
        return redirect('projects:detail', pk=pk)


class ProjectUpdateCreateView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_view(request.user):
            raise PermissionDenied
        form = ProjectUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.project = project
            update.author = request.user
            update.save()
            if _is_ajax(request):
                project = get_object_or_404(Project.objects.prefetch_related('updates__author'), pk=pk)
                return JsonResponse({
                    'ok': True,
                    'panel_html': _render_updates_panel(request, project),
                })
            messages.success(request, 'Atualização registrada.')
        else:
            if _is_ajax(request):
                return JsonResponse({
                    'ok': False,
                    'panel_html': _render_updates_panel(request, project, form),
                }, status=400)
            messages.error(request, 'Erro ao registrar atualização.')
        return redirect('projects:detail', pk=pk)


class ProjectUpdateDeleteView(TechnicianRequiredMixin, View):
    def post(self, request, pk, update_pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_view(request.user):
            raise PermissionDenied
        update = get_object_or_404(ProjectUpdate, pk=update_pk, project=project)
        if update.author == request.user or request.user.is_supervisor:
            update.delete()
            if _is_ajax(request):
                project = get_object_or_404(Project.objects.prefetch_related('updates__author'), pk=pk)
                return JsonResponse({
                    'ok': True,
                    'panel_html': _render_updates_panel(request, project),
                })
            messages.success(request, 'Atualização removida.')
        else:
            if _is_ajax(request):
                return JsonResponse({
                    'ok': False,
                    'panel_html': _render_updates_panel(request, project),
                }, status=403)
            messages.error(request, 'Sem permissão para remover esta atualização.')
        return redirect('projects:detail', pk=pk)
