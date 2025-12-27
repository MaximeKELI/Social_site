from django.contrib import admin
from .models import School, Student, Post, Comment, Conversation, Message, Notification, Group, Event


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'school', 'email', 'status', 'graduation_year', 'created_at', 'is_active')
    list_filter = ('status', 'school', 'is_active', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'school', 'created_at', 'like_count')
    list_filter = ('school', 'created_at')
    search_fields = ('title', 'content')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'is_group_chat', 'created_at', 'updated_at')
    list_filter = ('is_group_chat', 'created_at')
    filter_horizontal = ('participants',)
    search_fields = ('group__name',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'related_group', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'creator', 'member_count', 'created_at', 'is_active')
    list_filter = ('school', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('members',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'organizer', 'start_date', 'end_date', 'attendee_count')
    list_filter = ('school', 'start_date', 'created_at')
    search_fields = ('title', 'description', 'location')
    filter_horizontal = ('attendees',)
