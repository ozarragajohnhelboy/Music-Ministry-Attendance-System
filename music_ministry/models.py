from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date
import hashlib


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
        ('technical', 'Technical'),
        ('dancer', 'Dancer'),
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
    notes = models.TextField(blank=True, help_text="Admin notes for assigned members")
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


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('event_assignment', 'Event Assignment'),
        ('lineup_approved', 'Lineup Approved'),
        ('lineup_rejected', 'Lineup Rejected'),
    ]
    
    recipient = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.name} - {self.title}"


class BibleBook(models.Model):
    TESTAMENT_CHOICES = [
        ('old', 'Old Testament'),
        ('new', 'New Testament'),
    ]
    
    name = models.CharField(max_length=50)
    testament = models.CharField(max_length=3, choices=TESTAMENT_CHOICES)
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['testament', 'order']
    
    def __str__(self):
        return self.name


class BibleVerse(models.Model):
    book = models.ForeignKey(BibleBook, on_delete=models.CASCADE, related_name='verses')
    chapter = models.PositiveIntegerField()
    verse_number = models.PositiveIntegerField()
    text = models.TextField()
    
    class Meta:
        ordering = ['book__order', 'chapter', 'verse_number']
        unique_together = ['book', 'chapter', 'verse_number']
    
    def __str__(self):
        return f"{self.book.name} {self.chapter}:{self.verse_number}"
    
    @property
    def reference(self):
        return f"{self.book.name} {self.chapter}:{self.verse_number}"


class DailyVerse(models.Model):
    date = models.DateField(unique=True)
    verse = models.ForeignKey(BibleVerse, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Daily Verse for {self.date}: {self.verse.reference}"
    
    @classmethod
    def get_todays_verse(cls):
        """Get today's verse, creating one if it doesn't exist"""
        today = date.today()
        try:
            return cls.objects.get(date=today)
        except cls.DoesNotExist:
            # Create a new daily verse based on today's date
            # Use date hash to ensure same verse for same day
            date_str = today.strftime('%Y-%m-%d')
            date_hash = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
            
            # Get total count of verses
            total_verses = BibleVerse.objects.count()
            if total_verses == 0:
                return None
            
            # Use hash to select verse index
            verse_index = date_hash % total_verses
            verse = BibleVerse.objects.all()[verse_index]
            
            return cls.objects.create(date=today, verse=verse)


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    response = models.TextField()
    is_bible_related = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Chat from {self.user.username} at {self.created_at}"