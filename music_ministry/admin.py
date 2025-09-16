from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Member, Event, EventAssignment


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'musician_role', 'is_active')
    list_filter = ('musician_role', 'is_active')
    search_fields = ('name', 'email')
    ordering = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'end_time')
    list_filter = ('date',)
    search_fields = ('title', 'description')
    ordering = ('-date', '-start_time')
    date_hierarchy = 'date'


@admin.register(EventAssignment)
class EventAssignmentAdmin(admin.ModelAdmin):
    list_display = ('event', 'member', 'assigned_role', 'is_backup')
    list_filter = ('assigned_role', 'is_backup', 'event__date')
    search_fields = ('event__title', 'member__name')
    ordering = ('-event__date', 'assigned_role', 'is_backup')