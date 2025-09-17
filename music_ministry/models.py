from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')


class Member(models.Model):
    MUSICIAN_ROLES = [
        ('worship_leader', 'Worship Leader'),
        ('guitarist', 'Guitarist'),
        ('keys', 'Keys'),
        ('drummer', 'Drummer'),
        ('bassist', 'Bassist'),
        ('vocalist', 'Vocalist'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    musician_role = models.CharField(max_length=20, choices=MUSICIAN_ROLES)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_musician_role_display()}"


class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.title} - {self.date}"


class EventAssignment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='assignments')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='assignments')
    assigned_role = models.CharField(max_length=20, choices=Member.MUSICIAN_ROLES)
    is_backup = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['event', 'member', 'assigned_role']
    
    def __str__(self):
        backup_text = " (Backup)" if self.is_backup else ""
        return f"{self.event.title} - {self.member.name} ({self.get_assigned_role_display()}){backup_text}"


class Lineup(models.Model):
    STATUS_CHOICES = [
        ('for_approval', 'For Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    SET_LIST_CHOICES = [
        ('1p1w1f', '1 Praise, 1 Worship, 1 Fellowship'),
        ('2p1w1f', '2 Praise, 1 Worship, 1 Fellowship'),
        ('2p2w1f', '2 Praise, 2 Worship, 1 Fellowship'),
        ('custom', 'Custom'),
    ]
    
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='lineup')
    set_list_type = models.CharField(max_length=10, choices=SET_LIST_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='for_approval')
    created_by = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='created_lineups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.event.title} - {self.get_set_list_type_display()} ({self.get_status_display()})"


class Song(models.Model):
    SONG_TYPE_CHOICES = [
        ('praise', 'Praise'),
        ('high_praise', 'High Praise'),
        ('worship', 'Worship'),
        ('high_worship', 'High Worship'),
        ('fellowship', 'Fellowship'),
    ]
    
    lineup = models.ForeignKey(Lineup, on_delete=models.CASCADE, related_name='songs')
    song_type = models.CharField(max_length=15, choices=SONG_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    song_link = models.URLField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order', 'song_type']
        unique_together = ['lineup', 'order']
    
    def __str__(self):
        return f"{self.get_song_type_display()}: {self.title}"