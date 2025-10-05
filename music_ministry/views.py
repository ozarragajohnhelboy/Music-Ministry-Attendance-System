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

from .models import User, Member, Event, EventAssignment, Lineup, Song, Notification, DailyVerse, ChatMessage
from .forms import CustomUserCreationForm, EventForm, EventAssignmentForm, LineupForm, SongForm, LineupApprovalForm
from .notifications import create_event_assignment_notifications, create_lineup_approval_notifications, get_unread_notifications_count, mark_notification_as_read, mark_all_notifications_as_read
from .email_service import send_event_assignment_emails, send_lineup_approval_emails
from .bible_service import BibleChatbot
from .openai_bible_service import OpenAIBibleService


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
    
    # Get today's daily verse
    daily_verse = DailyVerse.get_todays_verse()
    
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
        'daily_verse': daily_verse,
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


@login_required
def bible_chatbot(request):
    """Bible chatbot page"""
    recent_messages = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'music_ministry/bible_chatbot.html', {
        'recent_messages': recent_messages
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_bible_chat(request):
    """API endpoint for Bible chatbot with conversational event creation"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Check if user is admin and if they want to create an event
        if request.user.role == 'admin':
            # Check for event creation intent
            event_keywords = ['create event', 'make event', 'new event', 'add event', 'schedule event']
            message_lower = message.lower()
            
            if any(keyword in message_lower for keyword in event_keywords):
                # Initialize event creation conversation
                request.session['event_creation_state'] = {
                    'step': 'title',
                    'data': {}
                }
                response = "Great! Let's create a new event. What is the title of the event?"
                return JsonResponse({
                    'response': response,
                    'is_bible_related': False,
                    'event_creation_mode': True
                })
            
            # Check if we're in event creation mode
            if 'event_creation_state' in request.session:
                return handle_event_creation_conversation(request, message)
        
        # Normal Bible chat flow
        try:
            # Initialize OpenAI Bible service
            openai_service = OpenAIBibleService()
            response, is_bible_related = openai_service.generate_response(message, request.user)
        except Exception as openai_error:
            print(f"OpenAI service error: {openai_error}")
            # Fallback to local Bible chatbot
            chatbot = BibleChatbot()
            response, is_bible_related = chatbot.generate_response(message, request.user)
            chatbot.save_conversation(request.user, message, response, is_bible_related)
        
        return JsonResponse({
            'response': response,
            'is_bible_related': is_bible_related
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def handle_event_creation_conversation(request, message):
    """Handle the conversational flow for event creation"""
    from difflib import get_close_matches
    
    state = request.session['event_creation_state']
    current_step = state['step']
    event_data = state['data']
    
    # Handle cancel command
    if message.lower() in ['cancel', 'stop', 'quit', 'exit']:
        del request.session['event_creation_state']
        return JsonResponse({
            'response': "Event creation cancelled. How else can I help you?",
            'is_bible_related': False
        })
    
    # Step 1: Get event title
    if current_step == 'title':
        event_data['title'] = message
        state['step'] = 'date'
        state['data'] = event_data
        request.session['event_creation_state'] = state
        return JsonResponse({
            'response': f"Great! Event title: '{message}'. When is the event? (Format: YYYY-MM-DD, e.g., 2025-10-12)",
            'is_bible_related': False,
            'event_creation_mode': True
        })
    
    # Step 2: Get date
    elif current_step == 'date':
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(message, '%Y-%m-%d')
            event_data['date'] = message
            state['step'] = 'start_time'
            state['data'] = event_data
            request.session['event_creation_state'] = state
            return JsonResponse({
                'response': f"Perfect! Date set to {message}. What time does the event start? (Format: HH:MM, e.g., 09:00)",
                'is_bible_related': False,
                'event_creation_mode': True
            })
        except ValueError:
            return JsonResponse({
                'response': "Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-10-12)",
                'is_bible_related': False,
                'event_creation_mode': True
            })
    
    # Step 3: Get start time
    elif current_step == 'start_time':
        # Validate time format
        try:
            from datetime import datetime
            datetime.strptime(message, '%H:%M')
            event_data['start_time'] = message
            state['step'] = 'end_time'
            state['data'] = event_data
            request.session['event_creation_state'] = state
            return JsonResponse({
                'response': f"Got it! Start time: {message}. What time does the event end? (Format: HH:MM, e.g., 11:00)",
                'is_bible_related': False,
                'event_creation_mode': True
            })
        except ValueError:
            return JsonResponse({
                'response': "Invalid time format. Please use HH:MM format (e.g., 09:00)",
                'is_bible_related': False,
                'event_creation_mode': True
            })
    
    # Step 4: Get end time
    elif current_step == 'end_time':
        try:
            from datetime import datetime
            datetime.strptime(message, '%H:%M')
            event_data['end_time'] = message
            state['step'] = 'worship_leaders'
            state['data'] = event_data
            request.session['event_creation_state'] = state
            return JsonResponse({
                'response': f"End time set to {message}. Now, who are the worship leaders? (Separate multiple names with commas, e.g., 'joy, irish')",
                'is_bible_related': False,
                'event_creation_mode': True
            })
        except ValueError:
            return JsonResponse({
                'response': "Invalid time format. Please use HH:MM format (e.g., 11:00)",
                'is_bible_related': False,
                'event_creation_mode': True
            })
    
    # Step 5: Get worship leaders
    elif current_step == 'worship_leaders':
        names = [name.strip() for name in message.split(',')]
        matched_members = find_members_by_names(names)
        
        if not matched_members:
            return JsonResponse({
                'response': f"I couldn't find any members matching '{message}'. Please try again with different names.",
                'is_bible_related': False,
                'event_creation_mode': True
            })
        
        event_data['worship_leaders'] = [m.id for m in matched_members]
        member_names = ', '.join([m.name for m in matched_members])
        state['step'] = 'backup_worship_leaders'
        state['data'] = event_data
        request.session['event_creation_state'] = state
        return JsonResponse({
            'response': f"Found worship leaders: {member_names}. Who are the backup worship leaders? (Separate with commas, or type 'empty' to skip)",
            'is_bible_related': False,
            'event_creation_mode': True
        })
    
    # Step 6: Get backup worship leaders
    elif current_step == 'backup_worship_leaders':
        if message.lower() in ['empty', 'skip', 'none', '']:
            event_data['backup_worship_leaders'] = []
            member_names = "None"
        else:
            names = [name.strip() for name in message.split(',')]
            matched_members = find_members_by_names(names)
            
            if not matched_members:
                return JsonResponse({
                    'response': f"I couldn't find any members matching '{message}'. Please try again or type 'empty' to skip.",
                    'is_bible_related': False,
                    'event_creation_mode': True
                })
            
            event_data['backup_worship_leaders'] = [m.id for m in matched_members]
            member_names = ', '.join([m.name for m in matched_members])
        
        state['step'] = 'guitarists'
        state['data'] = event_data
        request.session['event_creation_state'] = state
        return JsonResponse({
            'response': f"Backup worship leaders: {member_names}. Who are the guitarists? (Separate with commas)",
            'is_bible_related': False,
            'event_creation_mode': True
        })
    
    # Step 7: Get guitarists
    elif current_step == 'guitarists':
        names = [name.strip() for name in message.split(',')]
        matched_members = find_members_by_names(names)
        
        if not matched_members:
            return JsonResponse({
                'response': f"I couldn't find any members matching '{message}'. Please try again with different names.",
                'is_bible_related': False,
                'event_creation_mode': True
            })
        
        event_data['guitarists'] = [m.id for m in matched_members]
        member_names = ', '.join([m.name for m in matched_members])
        state['step'] = 'keys_player'
        state['data'] = event_data
        request.session['event_creation_state'] = state
        return JsonResponse({
            'response': f"Found guitarists: {member_names}. Who is the keys player? (Type a name, or 'empty' to skip)",
            'is_bible_related': False,
            'event_creation_mode': True
        })
    
    # Step 8: Get keys player
    elif current_step == 'keys_player':
        if message.lower() in ['empty', 'skip', 'none', '']:
            event_data['keys_player'] = None
            member_name = "None"
        else:
            matched_members = find_members_by_names([message])
            
            if not matched_members:
                return JsonResponse({
                    'response': f"I couldn't find any member matching '{message}'. Please try again or type 'empty' to skip.",
                    'is_bible_related': False,
                    'event_creation_mode': True
                })
            
            event_data['keys_player'] = matched_members[0].id
            member_name = matched_members[0].name
        
        state['step'] = 'drummer'
        state['data'] = event_data
        request.session['event_creation_state'] = state
        return JsonResponse({
            'response': f"Keys player: {member_name}. Who is the drummer? (Type a name, or 'empty' to skip)",
            'is_bible_related': False,
            'event_creation_mode': True
        })
    
    # Step 9: Get drummer
    elif current_step == 'drummer':
        if message.lower() in ['empty', 'skip', 'none', '']:
            event_data['drummer'] = None
            member_name = "None"
        else:
            matched_members = find_members_by_names([message])
            
            if not matched_members:
                return JsonResponse({
                    'response': f"I couldn't find any member matching '{message}'. Please try again or type 'empty' to skip.",
                    'is_bible_related': False,
                    'event_creation_mode': True
                })
            
            event_data['drummer'] = matched_members[0].id
            member_name = matched_members[0].name
        
        state['step'] = 'bassist'
        state['data'] = event_data
        request.session['event_creation_state'] = state
        return JsonResponse({
            'response': f"Drummer: {member_name}. Who is the bassist? (Type a name, or 'empty' to skip)",
            'is_bible_related': False,
            'event_creation_mode': True
        })
    
    # Step 10: Get bassist and create event
    elif current_step == 'bassist':
        if message.lower() in ['empty', 'skip', 'none', '']:
            event_data['bassist'] = None
            member_name = "None"
        else:
            matched_members = find_members_by_names([message])
            
            if not matched_members:
                return JsonResponse({
                    'response': f"I couldn't find any member matching '{message}'. Please try again or type 'empty' to skip.",
                    'is_bible_related': False,
                    'event_creation_mode': True
                })
            
            event_data['bassist'] = matched_members[0].id
            member_name = matched_members[0].name
        
        # Create the event
        try:
            result = create_event_from_conversation(event_data)
            del request.session['event_creation_state']
            
            return JsonResponse({
                'response': f"✅ Perfect! Event '{event_data['title']}' has been created successfully!\n\nAll assigned members have been notified via email. The event is now visible on the calendar.",
                'is_bible_related': False,
                'event_created': True,
                'event_id': result['event_id']
            })
        except Exception as e:
            del request.session['event_creation_state']
            return JsonResponse({
                'response': f"❌ Sorry, there was an error creating the event: {str(e)}\n\nPlease try again or create the event manually.",
                'is_bible_related': False,
                'error': True
            })


def find_members_by_names(names):
    """Find members by partial name matching"""
    from difflib import get_close_matches
    
    matched_members = []
    all_members = Member.objects.filter(is_active=True)
    
    for name in names:
        name = name.strip().lower()
        if not name:
            continue
        
        # Try exact match first
        exact_match = all_members.filter(name__icontains=name).first()
        if exact_match:
            matched_members.append(exact_match)
            continue
        
        # Try fuzzy matching
        all_member_names = [m.name.lower() for m in all_members]
        close_matches = get_close_matches(name, all_member_names, n=1, cutoff=0.6)
        
        if close_matches:
            matched_member = all_members.filter(name__icontains=close_matches[0]).first()
            if matched_member:
                matched_members.append(matched_member)
    
    return matched_members


def create_event_from_conversation(event_data):
    """Create event from conversational data"""
    with transaction.atomic():
        # Create event
        event = Event.objects.create(
            title=event_data['title'],
            date=event_data['date'],
            start_time=event_data['start_time'],
            end_time=event_data['end_time'],
            description='',
            notes=''
        )
        
        # Assign worship leaders
        for leader_id in event_data.get('worship_leaders', []):
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
        
        # Assign backup worship leaders
        for leader_id in event_data.get('backup_worship_leaders', []):
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
        
        # Assign guitarists
        for guitarist_id in event_data.get('guitarists', []):
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
        
        # Assign keys player (optional)
        keys_player_id = event_data.get('keys_player')
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
        
        # Assign drummer (optional)
        drummer_id = event_data.get('drummer')
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
        
        # Assign bassist (optional)
        bassist_id = event_data.get('bassist')
        if bassist_id:
            try:
                member = Member.objects.get(id=bassist_id)
                EventAssignment.objects.create(
                    event=event,
                    member=member,
                    assigned_role='bassist',
                    is_backup=False
                )
            except Member.DoesNotExist:
                pass
        
        # Send notifications and emails
        assigned_assignments = EventAssignment.objects.filter(event=event)
        if assigned_assignments.exists():
            event.refresh_from_db()
            assigned_members = [assignment.member for assignment in assigned_assignments]
            create_event_assignment_notifications(event, assigned_members)
            send_event_assignment_emails(event)
        
        return {
            'success': True,
            'event_id': event.id,
            'message': f'Event "{event.title}" created successfully!'
        }


@login_required
@require_http_methods(["GET"])
def api_daily_verse(request):
    """API endpoint to get today's daily verse"""
    daily_verse = DailyVerse.get_todays_verse()
    
    if daily_verse:
        return JsonResponse({
            'verse': {
                'reference': daily_verse.verse.reference,
                'text': daily_verse.verse.text,
                'book': daily_verse.verse.book.name,
                'testament': daily_verse.verse.book.get_testament_display()
            },
            'date': daily_verse.date.strftime('%Y-%m-%d')
        })
    else:
        return JsonResponse({'error': 'No daily verse available'}, status=404)


@csrf_exempt
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_create_event_from_chat(request):
    """API endpoint to create event from Bible Assistant chat"""
    try:
        data = json.loads(request.body)
        
        # Log the received data for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Received event data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'date', 'start_time', 'end_time', 'worship_leaders', 'backup_worship_leaders', 'guitarists']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'Missing required field: {field}'}, status=400)
        
        # Validate that required fields have at least one selection
        if not data.get('worship_leaders') or len(data.get('worship_leaders', [])) == 0:
            return JsonResponse({'success': False, 'error': 'At least one worship leader is required'}, status=400)
        
        if not data.get('backup_worship_leaders') or len(data.get('backup_worship_leaders', [])) == 0:
            return JsonResponse({'success': False, 'error': 'At least one backup worship leader is required'}, status=400)
        
        if not data.get('guitarists') or len(data.get('guitarists', [])) == 0:
            return JsonResponse({'success': False, 'error': 'At least one guitarist is required'}, status=400)
        
        with transaction.atomic():
            # Create event
            event = Event.objects.create(
                title=data['title'],
                date=data['date'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                description=data.get('description', ''),
                notes=data.get('notes', '')
            )
            
            # Assign worship leaders
            for leader_id in data.get('worship_leaders', []):
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
            
            # Assign backup worship leaders
            for leader_id in data.get('backup_worship_leaders', []):
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
            
            # Assign guitarists
            for guitarist_id in data.get('guitarists', []):
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
            
            # Assign keys player (optional)
            keys_player_id = data.get('keys_player')
            if keys_player_id and keys_player_id != '':
                try:
                    member = Member.objects.get(id=keys_player_id)
                    EventAssignment.objects.create(
                        event=event,
                        member=member,
                        assigned_role='keys',
                        is_backup=False
                    )
                except (Member.DoesNotExist, ValueError):
                    pass
            
            # Assign drummer (optional)
            drummer_id = data.get('drummer')
            if drummer_id and drummer_id != '':
                try:
                    member = Member.objects.get(id=drummer_id)
                    EventAssignment.objects.create(
                        event=event,
                        member=member,
                        assigned_role='drummer',
                        is_backup=False
                    )
                except (Member.DoesNotExist, ValueError):
                    pass
            
            # Assign bassist (optional)
            bass_player_id = data.get('bass_player')
            if bass_player_id and bass_player_id != '':
                try:
                    member = Member.objects.get(id=bass_player_id)
                    EventAssignment.objects.create(
                        event=event,
                        member=member,
                        assigned_role='bassist',
                        is_backup=False
                    )
                except (Member.DoesNotExist, ValueError):
                    pass
            
            # Send notifications and emails
            assigned_assignments = EventAssignment.objects.filter(event=event)
            if assigned_assignments.exists():
                event.refresh_from_db()
                # Extract Member objects from EventAssignment objects
                assigned_members = [assignment.member for assignment in assigned_assignments]
                create_event_assignment_notifications(event, assigned_members)
                send_event_assignment_emails(event)
        
        return JsonResponse({
            'success': True,
            'event_id': event.id,
            'message': f'Event "{event.title}" created successfully!'
        })
        
    except json.JSONDecodeError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating event: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

