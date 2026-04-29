from django.contrib import admin
from .models import Project, ProjectMember, ProjectTask, ProjectUpdate


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    raw_id_fields = ('user', 'added_by')


class ProjectTaskInline(admin.TabularInline):
    model = ProjectTask
    extra = 0
    fields = ('title', 'status', 'priority', 'assignee', 'due_date')
    raw_id_fields = ('assignee', 'created_by')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'area', 'status', 'priority', 'responsible', 'start_date', 'end_date')
    list_filter = ('status', 'priority', 'area')
    search_fields = ('code', 'name', 'description')
    raw_id_fields = ('responsible', 'created_by')
    inlines = [ProjectMemberInline, ProjectTaskInline]


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'status', 'priority', 'assignee', 'due_date')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'project__name', 'project__code')
    raw_id_fields = ('project', 'assignee', 'created_by')


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ('project', 'author', 'created_at')
    list_filter = ('project',)
    raw_id_fields = ('project', 'author')
