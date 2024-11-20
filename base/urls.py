from django.contrib import admin
from django.urls import path
from django.urls.conf import include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('createteam/', views.createteam, name='createteam'),
    path('addmember/', views.addmember, name='addmember'),
    path('acceptinvite/<str:teamname>/', views.acceptinvite, name='acceptinvite'),
    path('rejectinvite/<str:teamname>/', views.rejectinvite, name='rejectinvite'),
    path('teams/', views.teams, name='teams'),
    path('team/<int:id>/', views.team, name='team'),
    path('team/<int:id>/delete/', views.delete_team, name='delete_team'),
    path('chatroom', views.chat_room, name='chatroom'),
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
    path('tags/', views.tags, name='tags'),
    path('uhackathon/<str:hack>/', views.register_hackathon, name='uhackathon'),
    path('searchhackathon/', views.searchhackathon, name='searchhackathon'),
    path('organization/<str:name>/', views.create_hackathon, name='organization'),
    path('chat/', views.chat, name='chat'),
    path('project', views.project, name='project'),
    path('hackathon/<int:hackathon_id>/', views.displayorghackathons, name='displayorghackathons'),
    path('add_tag/', views.add_tag, name='add_tag'),  # New URL pattern
    path('project/<int:id>/', views.project, name='project'),
] 