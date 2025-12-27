from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import school_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/school/', views.register_school, name='register_school'),
    path('register/student/', views.register_student, name='register_student'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
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
    path('group/<int:group_id>/chat/', views.group_chat, name='group_chat'),
    path('group/create/', views.create_group, name='create_group'),
    
    # Events
    path('events/', views.events_list, name='events_list'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/create/', views.create_event, name='create_event'),
    
    # School features
    path('school/groups/', school_views.school_groups_list, name='school_groups_list'),
    path('school/group/<int:group_id>/', school_views.school_group_detail, name='school_group_detail'),
    path('school/group/create/', school_views.school_create_group, name='school_create_group'),
    path('school/events/', school_views.school_events_list, name='school_events_list'),
    path('school/event/<int:event_id>/', school_views.school_event_detail, name='school_event_detail'),
    path('school/event/create/', school_views.school_create_event, name='school_create_event'),
    path('school/conversations/', school_views.school_conversations_list, name='school_conversations_list'),
    path('school/conversation/<int:conversation_id>/', school_views.school_conversation_detail, name='school_conversation_detail'),
    path('school/conversation/start/<int:student_id>/', school_views.school_start_conversation, name='school_start_conversation'),
    path('school/notifications/', school_views.school_notifications, name='school_notifications'),
    path('school/statistics/', school_views.school_statistics, name='school_statistics'),
    path('school/statistics/chart/<str:chart_type>/', school_views.school_statistics_chart, name='school_statistics_chart'),
    path('school/export/csv/', school_views.school_export_csv, name='school_export_csv'),
    path('school/export/pdf/', school_views.school_export_pdf, name='school_export_pdf'),
]


