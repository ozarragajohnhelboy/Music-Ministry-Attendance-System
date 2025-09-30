from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Member, Event, EventAssignment
import logging

logger = logging.getLogger(__name__)

def send_event_assignment_emails(event):
    """
    Send email notifications to all members assigned to an event.
    """
    try:
        # Get all assigned members for this event
        assignments = EventAssignment.objects.filter(event=event)
        
        if not assignments.exists():
            logger.info(f"No assigned members found for event: {event.title}")
            return
        
        # Get all assigned members
        assigned_members = [assignment.member for assignment in assignments]
        
        # Prepare email data
        subject = f"Event Assignment: {event.title}"
        app_url = getattr(settings, 'APP_URL', 'http://localhost:8000')
        
        for member in assigned_members:
            try:
                # Render email template
                html_message = render_to_string('emails/event_assignment.html', {
                    'member': member,
                    'event': event,
                    'assigned_members': assignments,
                    'app_url': app_url
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message=f"Hi {member.name}, you have been assigned to {event.title} on {event.date}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[member.email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                logger.info(f"Event assignment email sent to {member.name} ({member.email})")
                
            except Exception as e:
                logger.error(f"Failed to send event assignment email to {member.name}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to send event assignment emails for event {event.title}: {str(e)}")


def send_lineup_approval_emails(lineup):
    """
    Send email notifications to technical and dancer members only when a lineup is approved.
    """
    try:
        event = lineup.event
        
        # Get ONLY technical and dancer members (regardless of event assignment)
        tech_dancer_members = Member.objects.filter(
            musician_role__in=['technical', 'dancer'],
            is_active=True
        )
        
        if not tech_dancer_members.exists():
            logger.info(f"No technical/dancer members found for lineup approval: {event.title}")
            return
        
        # Prepare email data
        subject = f"Lineup Approved: {event.title}"
        app_url = getattr(settings, 'APP_URL', 'http://localhost:8000')
        
        for member in tech_dancer_members:
            try:
                # Render email template
                html_message = render_to_string('emails/lineup_approved.html', {
                    'member': member,
                    'event': event,
                    'lineup': lineup,
                    'app_url': app_url
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message=f"Hi {member.name}, the lineup for {event.title} has been approved.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[member.email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                logger.info(f"Lineup approval email sent to {member.name} ({member.email})")
                
            except Exception as e:
                logger.error(f"Failed to send lineup approval email to {member.name}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to send lineup approval emails for lineup {lineup.id}: {str(e)}")


