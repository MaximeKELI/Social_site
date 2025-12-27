from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/school/', views.register_school, name='register_school'),
    path('register/student/', views.register_student, name='register_student'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('school/dashboard/', views.school_dashboard, name='school_dashboard'),
    
    # Posts
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    
    # Students
    path('students/', views.student_list, name='student_list'),
    path('student/<int:student_id>/', views.student_profile, name='student_profile'),
    
    # Conversations
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/start/<int:student_id>/', views.start_conversation, name='start_conversation'),
    
    # Profile
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # Groups
    path('groups/', views.groups_list, name='groups_list'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('group/create/', views.create_group, name='create_group'),
    
    # Events
    path('events/', views.events_list, name='events_list'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/create/', views.create_event, name='create_event'),
]


