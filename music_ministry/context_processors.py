from .models import Member


def members_data(request):
    """
    Context processor to make member data available in all templates,
    especially for the Bible Assistant event creation form in base.html
    """
    if request.user.is_authenticated and request.user.role == 'admin':
        return {
            'worship_leaders': Member.objects.filter(musician_role='worship_leader', is_active=True),
            'guitarists': Member.objects.filter(musician_role='guitarist', is_active=True),
            'keys_players': Member.objects.filter(musician_role='keys', is_active=True),
            'drummers': Member.objects.filter(musician_role='drummer', is_active=True),
            'bassists': Member.objects.filter(musician_role='bassist', is_active=True),
        }
    return {}
