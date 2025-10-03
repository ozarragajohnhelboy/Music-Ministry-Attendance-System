from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('event/add/', views.add_event, name='add_event'),
    path('assign-members/<int:event_id>/', views.assign_members, name='assign_members'),
    path('api/event-assignments/<int:event_id>/', views.get_event_assignments, name='get_event_assignments'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('api/events/', views.api_events, name='api_events'),
    path('api/notifications/', views.api_notifications, name='api_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.api_mark_notification_read, name='api_mark_notification_read'),
    path('api/notifications/<int:notification_id>/delete/', views.api_delete_notification, name='api_delete_notification'),
    path('api/notifications/mark-all-read/', views.api_mark_all_notifications_read, name='api_mark_all_notifications_read'),
    path('lineups/', views.lineups_view, name='lineups'),
    path('lineup/create/<int:event_id>/', views.create_lineup, name='create_lineup'),
    path('lineup/edit/<int:event_id>/', views.edit_lineup, name='edit_lineup'),
    path('lineup/approve/<int:event_id>/', views.approve_lineup, name='approve_lineup'),
    path('bible-chatbot/', views.bible_chatbot, name='bible_chatbot'),
    path('api/bible-chat/', views.api_bible_chat, name='api_bible_chat'),
    path('api/daily-verse/', views.api_daily_verse, name='api_daily_verse'),
]
