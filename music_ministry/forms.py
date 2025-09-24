from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Member, Event, EventAssignment, Lineup, Song


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=100, required=True)
    musician_role = forms.ChoiceField(choices=Member.MUSICIAN_ROLES, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'musician_role', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'member'  # All registered users are members by default
        if commit:
            user.save()
            Member.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                email=self.cleaned_data['email'],
                musician_role=self.cleaned_data['musician_role']
            )
        return user


class EventForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    
    class Meta:
        model = Event
        fields = ['title', 'date', 'start_time', 'end_time', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class EventAssignmentForm(forms.ModelForm):
    worship_leaders = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='worship_leader', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    guitarists = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='guitarist', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    keys_players = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='keys', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    drummers = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='drummer', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    bassists = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='bassist', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    vocalists = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='vocalist', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    backup_worship_leaders = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='worship_leader', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    backup_guitarists = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(musician_role='guitarist', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = EventAssignment
        fields = []


class LineupForm(forms.ModelForm):
    set_list_type = forms.ChoiceField(
        choices=Lineup.SET_LIST_CHOICES,
        widget=forms.Select(attrs={'id': 'setListType', 'onchange': 'updateSongFields()'})
    )
    
    class Meta:
        model = Lineup
        fields = ['set_list_type']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['set_list_type'].widget.attrs.update({'class': 'form-input form-select'})


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['song_type', 'title', 'song_link', 'order']
        widgets = {
            'song_type': forms.Select(attrs={'class': 'form-input form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Song title'}),
            'song_link': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'Song link (optional)'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
        }


class LineupApprovalForm(forms.ModelForm):
    class Meta:
        model = Lineup
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input form-select'})
        }
