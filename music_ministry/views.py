from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from datetime import datetime, date
import json

from .models import User, Member, Event, EventAssignment
from .forms import CustomUserCreationForm, EventForm, EventAssignmentForm


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    # All users can see all events (view access)
    events = Event.objects.all().order_by('date', 'start_time')
    upcoming_events = Event.objects.filter(date__gte=date.today()).order_by('date', 'start_time')[:5]
    
    # Get members by role for the modal
    worship_leaders = Member.objects.filter(musician_role='worship_leader', is_active=True)
    guitarists = Member.objects.filter(musician_role='guitarist', is_active=True)
    keys_players = Member.objects.filter(musician_role='keys', is_active=True)
    drummers = Member.objects.filter(musician_role='drummer', is_active=True)
    bassists = Member.objects.filter(musician_role='bassist', is_active=True)
    vocalists = Member.objects.filter(musician_role='vocalist', is_active=True)
    
    return render(request, 'music_ministry/dashboard.html', {
        'events': events,
        'upcoming_events': upcoming_events,
        'worship_leaders': worship_leaders,
        'guitarists': guitarists,
        'keys_players': keys_players,
        'drummers': drummers,
        'bassists': bassists,
        'vocalists': vocalists,
    })


@login_required
@user_passes_test(is_admin)
def add_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        event = Event.objects.create(
            title=title,
            date=date,
            start_time=start_time,
            end_time=end_time,
            description=request.POST.get('description', '')
        )
        
        # Handle multiple worship leaders
        worship_leader_ids = request.POST.getlist('worship_leaders')
        for leader_id in worship_leader_ids:
            try:
                member = Member.objects.get(id=leader_id)
                EventAssignment.objects.create(
                    event=event,
                    member=member,
                    assigned_role='worship_leader',
                    is_backup=False
                )
            except Member.DoesNotExist:
                pass
        
        # Handle multiple backup worship leaders
        backup_leader_ids = request.POST.getlist('backup_worship_leaders')
        for leader_id in backup_leader_ids:
            try:
                member = Member.objects.get(id=leader_id)
                EventAssignment.objects.create(
                    event=event,
                    member=member,
                    assigned_role='worship_leader',
                    is_backup=True
                )
            except Member.DoesNotExist:
                pass
        
        # Handle multiple guitarists
        guitarist_ids = request.POST.getlist('guitarists')
        for guitarist_id in guitarist_ids:
            try:
                member = Member.objects.get(id=guitarist_id)
                EventAssignment.objects.create(
                    event=event,
                    member=member,
                    assigned_role='guitarist',
                    is_backup=False
                )
            except Member.DoesNotExist:
                pass
        
        # Handle keys player assignment
        keys_player_id = request.POST.get('keys_player')
        if keys_player_id:
            try:
                member = Member.objects.get(id=keys_player_id)
                EventAssignment.objects.create(
                    event=event,
                    member=member,
                    assigned_role='keys',
                    is_backup=False
                )
            except Member.DoesNotExist:
                pass
        
        # Handle bass player assignment
        bass_player_id = request.POST.get('bass_player')
        if bass_player_id:
            try:
                member = Member.objects.get(id=bass_player_id)
                EventAssignment.objects.create(
                    event=event,
                    member=member,
                    assigned_role='bassist',
                    is_backup=False
                )
            except Member.DoesNotExist:
                pass
        
        # Handle drummer assignment
        drummer_id = request.POST.get('drummer')
        if drummer_id:
            try:
                member = Member.objects.get(id=drummer_id)
                EventAssignment.objects.create(
                    event=event,
                    member=member,
                    assigned_role='drummer',
                    is_backup=False
                )
            except Member.DoesNotExist:
                pass
        
        messages.success(request, 'Event created successfully with team assignments!')
        return redirect('dashboard')
    else:
        form = EventForm()
    return render(request, 'music_ministry/add_event.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def assign_members(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            EventAssignment.objects.filter(event=event).delete()
            
            role_fields = {
                'worship_leaders': 'worship_leader',
                'guitarists': 'guitarist', 
                'keys_player': 'keys',
                'drummer': 'drummer',
                'bass_player': 'bassist'
            }
            
            backup_fields = {
                'backup_worship_leaders': 'worship_leader'
            }
            
            for field_name, role in role_fields.items():
                if field_name in ['keys_player', 'drummer', 'bass_player']:
                    member_id = request.POST.get(field_name)
                    if member_id:
                        try:
                            member = Member.objects.get(id=member_id)
                            EventAssignment.objects.create(
                                event=event,
                                member=member,
                                assigned_role=role,
                                is_backup=False
                            )
                        except Member.DoesNotExist:
                            pass
                else:
                    member_ids = request.POST.getlist(field_name)
                    for member_id in member_ids:
                        try:
                            member = Member.objects.get(id=member_id)
                            EventAssignment.objects.create(
                                event=event,
                                member=member,
                                assigned_role=role,
                                is_backup=False
                            )
                        except Member.DoesNotExist:
                            pass
            
            for field_name, role in backup_fields.items():
                member_ids = request.POST.getlist(field_name)
                for member_id in member_ids:
                    member = get_object_or_404(Member, id=member_id)
                    EventAssignment.objects.create(
                        event=event,
                        member=member,
                        assigned_role=role,
                        is_backup=True
                    )
        
        messages.success(request, 'Member assignments updated successfully!')
        return redirect('dashboard')
    
    form = EventAssignmentForm()
    current_assignments = EventAssignment.objects.filter(event=event)
    
    return render(request, 'music_ministry/assign_members.html', {
        'event': event,
        'form': form,
        'current_assignments': current_assignments
    })


@login_required
@user_passes_test(is_admin)
def delete_event(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" has been deleted successfully!')
        return redirect('dashboard')
    else:
        return redirect('dashboard')


@login_required
@require_http_methods(["GET"])
def api_events(request):
    # All users can see all events in calendar
    events = Event.objects.all()
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'start': f"{event.date}T{event.start_time}",
            'end': f"{event.date}T{event.end_time}"
        })
    
    return JsonResponse(events_data, safe=False)