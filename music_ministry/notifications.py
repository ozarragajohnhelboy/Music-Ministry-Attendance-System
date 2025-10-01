from django.utils import timezone
from .models import Notification, Event, EventAssignment, Member


def create_event_assignment_notifications(event, assigned_members, notification_type='added'):
    """
    Create notifications for members when they are assigned to an event or removed from an event.
    """
    notifications = []
    
    # Ensure we have a fresh event object from the database
    try:
        event_obj = Event.objects.get(id=event.id)
    except Event.DoesNotExist:
        return notifications
    
    # Format date and time safely
    date_str = event_obj.date.strftime("%B %d, %Y") if hasattr(event_obj.date, 'strftime') else str(event_obj.date)
    time_str = event_obj.start_time.strftime("%I:%M %p") if hasattr(event_obj.start_time, 'strftime') else str(event_obj.start_time)
    
    for member in assigned_members:
        if notification_type == 'added':
            # Member was added to the event
            notification = Notification.objects.create(
                recipient=member,
                notification_type='event_assignment',
                title=f'You have been assigned to {event_obj.title}',
                message=f'You have been assigned to the event "{event_obj.title}" on {date_str} at {time_str}.',
                event=event_obj
            )
        elif notification_type == 'removed':
            # Member was removed from the event
            notification = Notification.objects.create(
                recipient=member,
                notification_type='event_removal',
                title=f'You have been removed from {event_obj.title}',
                message=f'You are no longer assigned to the event "{event_obj.title}" on {date_str} at {time_str}.',
                event=event_obj
            )
        else:
            # Default behavior for backward compatibility
            notification = Notification.objects.create(
                recipient=member,
                notification_type='event_assignment',
                title=f'You have been assigned to {event_obj.title}',
                message=f'You have been assigned to the event "{event_obj.title}" on {date_str} at {time_str}.',
                event=event_obj
            )
        
        notifications.append(notification)
    
    return notifications


def create_lineup_approval_notifications(lineup, status):
    """
    Create notifications for all members assigned to an event when lineup is approved/rejected.
    """
    notifications = []
    event = lineup.event
    
    # Get all members assigned to this event
    assigned_members = EventAssignment.objects.filter(event=event).select_related('member')
    
    if status == 'approved':
        title = f'Lineup approved for {event.title}'
        message = f'The lineup for "{event.title}" has been approved. You can now view the songs for this event.'
    elif status == 'rejected':
        title = f'Lineup rejected for {event.title}'
        message = f'The lineup for "{event.title}" has been rejected. Please check with the worship leader for updates.'
    else:
        return notifications  # Don't create notifications for other statuses
    
    for assignment in assigned_members:
        notification = Notification.objects.create(
            recipient=assignment.member,
            notification_type=f'lineup_{status}',
            title=title,
            message=message,
            event=event
        )
        notifications.append(notification)
    
    return notifications


def get_unread_notifications_count(member):
    """
    Get the count of unread notifications for a member.
    """
    return Notification.objects.filter(recipient=member, is_read=False).count()


def mark_notification_as_read(notification_id, member):
    """
    Mark a specific notification as read for a member.
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=member)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False


def mark_all_notifications_as_read(member):
    """
    Mark all notifications as read for a member.
    """
    updated_count = Notification.objects.filter(recipient=member, is_read=False).update(is_read=True)
    return updated_count
