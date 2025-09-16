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
]
