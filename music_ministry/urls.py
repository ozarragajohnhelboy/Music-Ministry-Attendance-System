from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('event/add/', views.add_event, name='add_event'),
    path('assign-members/<int:event_id>/', views.assign_members, name='assign_members'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('api/events/', views.api_events, name='api_events'),
    path('lineups/', views.lineups_view, name='lineups'),
    path('lineup/create/<int:event_id>/', views.create_lineup, name='create_lineup'),
    path('lineup/edit/<int:event_id>/', views.edit_lineup, name='edit_lineup'),
    path('lineup/approve/<int:event_id>/', views.approve_lineup, name='approve_lineup'),
]
