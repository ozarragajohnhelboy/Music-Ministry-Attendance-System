from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction
from datetime import datetime, date
import json

from .models import User, Member, Event, EventAssignment, Lineup, Song, Notification
from .forms import CustomUserCreationForm, EventForm, EventAssignmentForm, LineupForm, SongForm, LineupApprovalForm
from .notifications import create_event_assignment_notifications, create_lineup_approval_notifications, get_unread_notifications_count, mark_notification_as_read, mark_all_notifications_as_read
from .email_service import send_event_assignment_emails, send_lineup_approval_emails


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
    
    current_member = None
    unread_notifications_count = 0
    can_create_events = False
    
    if hasattr(request.user, 'member'):
        current_member = request.user.member
        unread_notifications_count = get_unread_notifications_count(current_member)
    
    # Only admin can create events
    if request.user.role == 'admin':
        can_create_events = True
    
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
        'events_with_lineups': events_with_lineups,
        'unread_notifications_count': unread_notifications_count,
        'can_create_events': can_create_events,
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
            description=request.POST.get('description', ''),
            notes=request.POST.get('notes', '')
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
        
        # Create notifications for assigned members
        assigned_members = EventAssignment.objects.filter(event=event)
        if assigned_members.exists():
            # Refresh event from database to ensure proper date/time objects
            event.refresh_from_db()
            create_event_assignment_notifications(event, assigned_members)
            # Send email notifications to all assigned members
            send_event_assignment_emails(event)
        
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
            # Update notes if provided, otherwise keep existing notes
            notes = request.POST.get('notes', '').strip()
            if notes:  # Only update if notes are provided (not blank)
                event.notes = notes
                event.save()
            
            # Get current assignments to track changes
            current_assignments = EventAssignment.objects.filter(event=event)
            current_assignments_by_role = {}
            for assignment in current_assignments:
                role = assignment.assigned_role
                if role not in current_assignments_by_role:
                    current_assignments_by_role[role] = {'regular': [], 'backup': []}
                if assignment.is_backup:
                    current_assignments_by_role[role]['backup'].append(assignment)
                else:
                    current_assignments_by_role[role]['regular'].append(assignment)
            
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
            
            # Track changes for notifications
            removed_members = []  # Members who were removed
            added_members = []    # Members who were added
            
            # Process each role field
            for field_name, role in role_fields.items():
                if field_name in ['keys_player', 'drummer', 'bass_player']:
                    # Single select fields
                    member_id = request.POST.get(field_name)
                    if member_id:
                        # User selected someone, check if it's different from current
                        current_members = [a.member for a in current_assignments_by_role.get(role, {}).get('regular', [])]
                        
                        try:
                            new_member = Member.objects.get(id=member_id)
                            
                            # Check if assignment changed
                            if not current_members or current_members[0] != new_member:
                                # Assignment changed
                                if current_members:
                                    removed_members.extend(current_members)
                                added_members.append(new_member)
                                
                                # Update the assignment
                                EventAssignment.objects.filter(event=event, assigned_role=role, is_backup=False).delete()
                                EventAssignment.objects.create(
                                    event=event,
                                    member=new_member,
                                    assigned_role=role,
                                    is_backup=False
                                )
                        except Member.DoesNotExist:
                            pass
                    # If no member selected, keep existing assignments (don't delete)
                else:
                    # Multiple select fields
                    member_ids = request.POST.getlist(field_name)
                    if member_ids:  # If something was selected
                        # User selected members, check if it's different from current
                        current_members = [a.member for a in current_assignments_by_role.get(role, {}).get('regular', [])]
                        current_member_ids = {m.id for m in current_members}
                        new_member_ids = {int(mid) for mid in member_ids}
                        
                        # Find removed and added members
                        removed_ids = current_member_ids - new_member_ids
                        added_ids = new_member_ids - current_member_ids
                        
                        if removed_ids or added_ids:
                            # Assignments changed
                            for member in current_members:
                                if member.id in removed_ids:
                                    removed_members.append(member)
                            
                            for member_id in added_ids:
                                try:
                                    member = Member.objects.get(id=member_id)
                                    added_members.append(member)
                                except Member.DoesNotExist:
                                    pass
                            
                            # Update the assignments
                            EventAssignment.objects.filter(event=event, assigned_role=role, is_backup=False).delete()
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
                    # If nothing was selected, keep existing assignments (don't delete)
            
            # Process backup fields
            for field_name, role in backup_fields.items():
                member_ids = request.POST.getlist(field_name)
                if member_ids:  # If something was selected
                    # User selected backup members, check if it's different from current
                    current_backup_members = [a.member for a in current_assignments_by_role.get(role, {}).get('backup', [])]
                    current_backup_member_ids = {m.id for m in current_backup_members}
                    new_backup_member_ids = {int(mid) for mid in member_ids}
                    
                    # Find removed and added backup members
                    removed_backup_ids = current_backup_member_ids - new_backup_member_ids
                    added_backup_ids = new_backup_member_ids - current_backup_member_ids
                    
                    if removed_backup_ids or added_backup_ids:
                        # Backup assignments changed
                        for member in current_backup_members:
                            if member.id in removed_backup_ids:
                                removed_members.append(member)
                        
                        for member_id in added_backup_ids:
                            try:
                                member = Member.objects.get(id=member_id)
                                added_members.append(member)
                            except Member.DoesNotExist:
                                pass
                        
                        # Update the backup assignments
                        EventAssignment.objects.filter(event=event, assigned_role=role, is_backup=True).delete()
                        for member_id in member_ids:
                            try:
                                member = Member.objects.get(id=member_id)
                                EventAssignment.objects.create(
                                    event=event,
                                    member=member,
                                    assigned_role=role,
                                    is_backup=True
                                )
                            except Member.DoesNotExist:
                                pass
                # If nothing was selected, keep existing backup assignments (don't delete)
        
            # Send notifications only to members whose assignments changed
            if removed_members or added_members:
                # Refresh event from database to ensure proper date/time objects
                event.refresh_from_db()
                
                # Send notifications to removed members
                if removed_members:
                    create_event_assignment_notifications(event, removed_members, notification_type='removed')
                    send_event_assignment_emails(event, removed_members, email_type='removed')
                
                # Send notifications to added members
                if added_members:
                    create_event_assignment_notifications(event, added_members, notification_type='added')
                    send_event_assignment_emails(event, added_members, email_type='added')
        
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
def get_event_assignments(request, event_id):
    """API endpoint to get current assignments for an event"""
    event = get_object_or_404(Event, id=event_id)
    current_assignments = EventAssignment.objects.filter(event=event)
    
    # Group assignments by role
    assignments_data = {}
    for assignment in current_assignments:
        role = assignment.assigned_role
        if role not in assignments_data:
            assignments_data[role] = {'regular': [], 'backup': []}
        
        member_data = {
            'id': assignment.member.id,
            'name': assignment.member.name
        }
        
        if assignment.is_backup:
            assignments_data[role]['backup'].append(member_data)
        else:
            assignments_data[role]['regular'].append(member_data)
    
    # Map roles to form field names
    role_to_field_mapping = {
        'worship_leader': 'worship_leaders',
        'guitarist': 'guitarists',
        'keys': 'keys_player',
        'drummer': 'drummer',
        'bassist': 'bass_player'
    }
    
    # Prepare response data
    response_data = {
        'notes': event.notes or '',
        'assignments': {}
    }
    
    for role, assignments in assignments_data.items():
        field_name = role_to_field_mapping.get(role)
        if field_name:
            if field_name in ['keys_player', 'drummer', 'bass_player']:
                # Single select fields
                if assignments['regular']:
                    response_data['assignments'][field_name] = assignments['regular'][0]['id']
            else:
                # Multiple select fields
                response_data['assignments'][field_name] = [m['id'] for m in assignments['regular']]
        
        # Handle backup fields
        if role == 'worship_leader' and assignments['backup']:
            response_data['assignments']['backup_worship_leaders'] = [m['id'] for m in assignments['backup']]
    
    return JsonResponse(response_data)


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
            
        # Create notifications for all assigned members
        if status in ['approved', 'rejected']:
            create_lineup_approval_notifications(lineup, status)
            # Send email notifications when lineup is approved
            if status == 'approved':
                send_lineup_approval_emails(lineup)
            
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


@login_required
@require_http_methods(["GET"])
def api_notifications(request):
    """
    API endpoint to fetch notifications for the current user.
    """
    if not hasattr(request.user, 'member'):
        return JsonResponse({'notifications': []})
    
    current_member = request.user.member
    notifications = Notification.objects.filter(recipient=current_member).order_by('-created_at')[:20]
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%b %d, %Y %I:%M %p'),
            'event_id': notification.event.id if notification.event else None,
            'event_title': notification.event.title if notification.event else None,
        })
    
    return JsonResponse({'notifications': notifications_data})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_mark_notification_read(request, notification_id):
    """
    API endpoint to mark a specific notification as read.
    """
    if not hasattr(request.user, 'member'):
        return JsonResponse({'success': False, 'error': 'User has no member profile'})
    
    current_member = request.user.member
    success = mark_notification_as_read(notification_id, current_member)
    
    if success:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Notification not found'})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_mark_all_notifications_read(request):
    """
    API endpoint to mark all notifications as read for the current user.
    """
    if not hasattr(request.user, 'member'):
        return JsonResponse({'success': False, 'error': 'User has no member profile'})
    
    current_member = request.user.member
    updated_count = mark_all_notifications_as_read(current_member)
    
    return JsonResponse({'success': True, 'updated_count': updated_count})


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def api_delete_notification(request, notification_id):
    """
    API endpoint to delete a specific notification.
    """
    if not hasattr(request.user, 'member'):
        return JsonResponse({'success': False, 'error': 'User has no member profile'})
    
    current_member = request.user.member
    
    try:
        notification = Notification.objects.get(id=notification_id, recipient=current_member)
        notification.delete()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})

