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