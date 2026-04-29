from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser
from .models import Project, ProjectMember


class ProjectFlowTests(TestCase):
    def setUp(self):
        self.supervisor = CustomUser.objects.create_user(
            email='supervisor@example.com',
            password='secret123',
            full_name='Supervisor',
            role=CustomUser.SUPERVISOR,
        )
        self.creator = CustomUser.objects.create_user(
            email='creator@example.com',
            password='secret123',
            full_name='Creator User',
            role=CustomUser.TECHNICIAN,
        )
        self.responsible = CustomUser.objects.create_user(
            email='responsible@example.com',
            password='secret123',
            full_name='Responsible User',
            role=CustomUser.TECHNICIAN,
        )
        self.other = CustomUser.objects.create_user(
            email='other@example.com',
            password='secret123',
            full_name='Other User',
            role=CustomUser.TECHNICIAN,
        )

    def _project_payload(self, **overrides):
        payload = {
            'name': 'Portal de Projetos',
            'description': 'Descricao do projeto',
            'objective': 'Centralizar o acompanhamento',
            'area': Project.DEVELOPMENT,
            'status': Project.PLANNING,
            'priority': Project.MEDIUM,
            'responsible': str(self.responsible.pk),
            'start_date': '2026-04-01',
            'end_date': '2026-05-01',
        }
        payload.update(overrides)
        return payload

    def test_create_project_adds_creator_and_responsible_as_members(self):
        self.client.force_login(self.creator)

        response = self.client.post(reverse('projects:create'), self._project_payload())

        self.assertRedirects(response, reverse('projects:detail', args=[Project.objects.get().pk]))
        project = Project.objects.get()
        self.assertTrue(project.code.startswith('PRJ-'))
        self.assertEqual(project.created_by, self.creator)
        self.assertTrue(
            ProjectMember.objects.filter(
                project=project,
                user=self.creator,
                role=ProjectMember.MANAGER,
            ).exists()
        )
        self.assertTrue(
            ProjectMember.objects.filter(
                project=project,
                user=self.responsible,
                role=ProjectMember.MANAGER,
            ).exists()
        )

    def test_list_only_shows_projects_visible_to_technician(self):
        visible_project = Project.objects.create(
            name='Visible',
            description='Descricao',
            objective='Objetivo',
            area=Project.DEVELOPMENT,
            responsible=self.creator,
            created_by=self.creator,
        )
        ProjectMember.objects.create(
            project=visible_project,
            user=self.creator,
            role=ProjectMember.MANAGER,
            added_by=self.supervisor,
        )
        hidden_project = Project.objects.create(
            name='Hidden',
            description='Descricao',
            objective='Objetivo',
            area=Project.DEVELOPMENT,
            responsible=self.other,
            created_by=self.other,
        )
        ProjectMember.objects.create(
            project=hidden_project,
            user=self.other,
            role=ProjectMember.MANAGER,
            added_by=self.supervisor,
        )

        self.client.force_login(self.creator)
        response = self.client.get(reverse('projects:list'))

        projects = list(response.context['projects'])
        self.assertEqual(projects, [visible_project])

    def test_outsider_cannot_view_project_detail(self):
        project = Project.objects.create(
            name='Restrito',
            description='Descricao',
            objective='Objetivo',
            area=Project.DEVELOPMENT,
            responsible=self.creator,
            created_by=self.creator,
        )
        ProjectMember.objects.create(
            project=project,
            user=self.creator,
            role=ProjectMember.MANAGER,
            added_by=self.creator,
        )

        self.client.force_login(self.other)
        response = self.client.get(reverse('projects:detail', args=[project.pk]))

        self.assertEqual(response.status_code, 403)

    def test_update_project_adds_new_responsible_to_members(self):
        project = Project.objects.create(
            name='Migracao',
            description='Descricao',
            objective='Objetivo',
            area=Project.DEVELOPMENT,
            responsible=self.creator,
            created_by=self.creator,
        )
        ProjectMember.objects.create(
            project=project,
            user=self.creator,
            role=ProjectMember.MANAGER,
            added_by=self.creator,
        )

        self.client.force_login(self.creator)
        response = self.client.post(
            reverse('projects:edit', args=[project.pk]),
            self._project_payload(responsible=str(self.responsible.pk), name='Migracao 2'),
        )

        self.assertRedirects(response, reverse('projects:detail', args=[project.pk]))
        project.refresh_from_db()
        self.assertEqual(project.responsible, self.responsible)
        self.assertTrue(
            ProjectMember.objects.filter(
                project=project,
                user=self.responsible,
                role=ProjectMember.MANAGER,
            ).exists()
        )
