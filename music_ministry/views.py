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

from .models import User, Member, Event, EventAssignment, Lineup, Song
from .forms import CustomUserCreationForm, EventForm, EventAssignmentForm, LineupForm, SongForm, LineupApprovalForm


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


def get_or_create_member_for_user(user):
    """
    Get or create a Member object for a user.
    For admin users who don't have Member objects, create a default one.
    """
    try:
        return user.member
    except Member.DoesNotExist:
        if user.role == 'admin':
            # Create a default member for admin users
            return Member.objects.create(
                user=user,
                name=user.get_full_name() or user.username,
                email=user.email or f"{user.username}@admin.local",
                musician_role='worship_leader'  # Default role for admin
            )
        else:
            raise Member.DoesNotExist("User does not have an associated Member object")


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
    events = Event.objects.all().order_by('date', 'start_time')
    upcoming_events = Event.objects.filter(date__gte=date.today()).order_by('date', 'start_time')[:5]
    
    worship_leaders = Member.objects.filter(musician_role='worship_leader', is_active=True)
    guitarists = Member.objects.filter(musician_role='guitarist', is_active=True)
    keys_players = Member.objects.filter(musician_role='keys', is_active=True)
    drummers = Member.objects.filter(musician_role='drummer', is_active=True)
    bassists = Member.objects.filter(musician_role='bassist', is_active=True)
    vocalists = Member.objects.filter(musician_role='vocalist', is_active=True)
    
    current_member = None
    if hasattr(request.user, 'member'):
        current_member = request.user.member
    
    events_with_lineups = []
    for event in events:
        lineup = getattr(event, 'lineup', None)
        can_edit = False
        
        if current_member and event.assignments.filter(member=current_member).exists():
            can_edit = True
        elif request.user.role == 'admin':
            can_edit = True
        
        events_with_lineups.append({
            'event': event,
            'lineup': lineup,
            'can_edit': can_edit
        })
    
    return render(request, 'music_ministry/dashboard.html', {
        'events': events,
        'upcoming_events': upcoming_events,
        'worship_leaders': worship_leaders,
        'guitarists': guitarists,
        'keys_players': keys_players,
        'drummers': drummers,
        'bassists': bassists,
        'vocalists': vocalists,
        'events_with_lineups': events_with_lineups,
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
    events = Event.objects.all()
    
    events_data = []
    for event in events:
        event_data = {
            'id': event.id,
            'title': event.title,
            'start': f"{event.date}T{event.start_time}",
            'end': f"{event.date}T{event.end_time}"
        }
        
        if hasattr(event, 'lineup') and event.lineup.status == 'approved':
            songs = event.lineup.songs.all()
            if songs:
                event_data['songs'] = []
                for song in songs:
                    event_data['songs'].append({
                        'type': song.get_song_type_display(),
                        'title': song.title,
                        'song_link': song.song_link
                    })
        
        events_data.append(event_data)
    
    return JsonResponse(events_data, safe=False)


@login_required
def lineups_view(request):
    return redirect('dashboard')


@login_required
def create_lineup(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    current_member = get_or_create_member_for_user(request.user)
    
    if not event.assignments.filter(member=current_member).exists() and request.user.role != 'admin':
        messages.error(request, 'You are not assigned to this event.')
        return redirect('dashboard')
    
    if hasattr(event, 'lineup'):
        messages.info(request, 'This event already has a lineup.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        set_list_type = request.POST.get('set_list_type')
        
        if not set_list_type:
            messages.error(request, 'Please select a set list type.')
            return render(request, 'music_ministry/create_lineup.html', {
                'event': event,
                'form': LineupForm()
            })
        
        with transaction.atomic():
            lineup = Lineup.objects.create(
                event=event,
                set_list_type=set_list_type,
                created_by=current_member
            )
            
            songs_created = 0
            
            song_data = {
                '1p1w1f': [
                    ('praise', 1), ('worship', 2), ('fellowship', 3)
                ],
                '2p1w1f': [
                    ('praise', 1), ('high_praise', 2), ('worship', 3), ('fellowship', 4)
                ],
                '2p2w1f': [
                    ('praise', 1), ('high_praise', 2), ('worship', 3), ('high_worship', 4), ('fellowship', 5)
                ]
            }
            
            if set_list_type in song_data:
                for song_type, order in song_data[set_list_type]:
                    title = request.POST.get(f'{set_list_type}_{song_type}_title', '').strip()
                    link = request.POST.get(f'{set_list_type}_{song_type}_link', '').strip()
                    
                    if title:
                        Song.objects.create(
                            lineup=lineup,
                            song_type=song_type,
                            title=title,
                            song_link=link,
                            order=order
                        )
                        songs_created += 1
            else:
                i = 1
                while True:
                    song_type = request.POST.get(f'custom_song_type_{i}')
                    song_title = request.POST.get(f'custom_song_title_{i}', '').strip()
                    song_link = request.POST.get(f'custom_song_link_{i}', '').strip()
                    
                    if not song_type or not song_title:
                        break
                    
                    Song.objects.create(
                        lineup=lineup,
                        song_type=song_type,
                        title=song_title,
                        song_link=song_link,
                        order=i
                    )
                    songs_created += 1
                    i += 1
            
            if songs_created == 0:
                messages.warning(request, 'Lineup created but no songs were added. Please make sure to fill in song titles.')
            else:
                messages.success(request, f'Lineup created successfully with {songs_created} songs!')
        
        return redirect('dashboard')
    
    return render(request, 'music_ministry/create_lineup.html', {
        'event': event,
        'form': LineupForm()
    })


@login_required
def edit_lineup(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    lineup = get_object_or_404(Lineup, event=event)
    current_member = get_or_create_member_for_user(request.user)
    
    if not event.assignments.filter(member=current_member).exists() and request.user.role != 'admin':
        messages.error(request, 'You are not assigned to this event.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        with transaction.atomic():
            lineup.songs.all().delete()
            
            set_list_type = request.POST.get('set_list_type', lineup.set_list_type)
            lineup.set_list_type = set_list_type
            lineup.save()
            
            songs_created = 0
            
            song_data = {
                '1p1w1f': [
                    ('praise', 1), ('worship', 2), ('fellowship', 3)
                ],
                '2p1w1f': [
                    ('praise', 1), ('high_praise', 2), ('worship', 3), ('fellowship', 4)
                ],
                '2p2w1f': [
                    ('praise', 1), ('high_praise', 2), ('worship', 3), ('high_worship', 4), ('fellowship', 5)
                ]
            }
            
            if set_list_type in song_data:
                for song_type, order in song_data[set_list_type]:
                    title = request.POST.get(f'{set_list_type}_{song_type}_title', '').strip()
                    link = request.POST.get(f'{set_list_type}_{song_type}_link', '').strip()
                    
                    if title:
                        Song.objects.create(
                            lineup=lineup,
                            song_type=song_type,
                            title=title,
                            song_link=link,
                            order=order
                        )
                        songs_created += 1
            else:
                i = 1
                while True:
                    song_type = request.POST.get(f'custom_song_type_{i}')
                    song_title = request.POST.get(f'custom_song_title_{i}', '').strip()
                    song_link = request.POST.get(f'custom_song_link_{i}', '').strip()
                    
                    if not song_type or not song_title:
                        break
                    
                    Song.objects.create(
                        lineup=lineup,
                        song_type=song_type,
                        title=song_title,
                        song_link=song_link,
                        order=i
                    )
                    songs_created += 1
                    i += 1
            
            if songs_created == 0:
                messages.warning(request, 'Lineup updated but no songs were added. Please make sure to fill in song titles.')
            else:
                messages.success(request, f'Lineup updated successfully with {songs_created} songs!')
        
        return redirect('dashboard')
    
    return render(request, 'music_ministry/edit_lineup.html', {
        'event': event,
        'lineup': lineup,
        'form': LineupForm(instance=lineup)
    })


@login_required
@user_passes_test(is_admin)
def approve_lineup(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    lineup = get_object_or_404(Lineup, event=event)
    
    if request.method == 'POST':
        form = LineupApprovalForm(request.POST, instance=lineup)
        if form.is_valid():
            form.save()
            status = form.cleaned_data['status']
            if status == 'approved':
                messages.success(request, 'Lineup approved successfully!')
            elif status == 'rejected':
                messages.success(request, 'Lineup rejected.')
            else:
                messages.success(request, 'Lineup status updated.')
            return redirect('dashboard')
    else:
        form = LineupApprovalForm(instance=lineup)
    
    return render(request, 'music_ministry/approve_lineup.html', {
        'event': event,
        'lineup': lineup,
        'form': form
    })