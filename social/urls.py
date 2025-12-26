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
]

