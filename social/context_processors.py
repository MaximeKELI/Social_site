"""
Context processors pour ajouter des données globales aux templates
"""
from .models import Conversation, Message, Notification


def user_notifications(request):
    """Ajoute le nombre de notifications et messages non lus au contexte"""
    context = {
        'unread_messages_count': 0,
        'unread_notifications_count': 0,
    }
    
    if request.user.is_authenticated:
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            
            # Calculer le nombre de messages non lus
            conversations = Conversation.objects.filter(participants_students=student)
            unread_messages_count = 0
            for conversation in conversations:
                unread = Message.objects.filter(
                    conversation=conversation
                ).exclude(sender_student=student).filter(is_read=False).count()
                unread_messages_count += unread
            
            # Calculer le nombre de notifications non lues
            unread_notifications_count = Notification.objects.filter(
                recipient_student=student,
                is_read=False
            ).count()
            
            context['unread_messages_count'] = unread_messages_count
            context['unread_notifications_count'] = unread_notifications_count
        
        elif hasattr(request.user, 'school_profile'):
            school = request.user.school_profile
            
            # Calculer le nombre de messages non lus
            conversations = Conversation.objects.filter(participants_schools=school)
            unread_messages_count = 0
            for conversation in conversations:
                unread = Message.objects.filter(
                    conversation=conversation
                ).exclude(sender_school=school).filter(is_read=False).count()
                unread_messages_count += unread
            
            # Calculer le nombre de notifications non lues
            unread_notifications_count = Notification.objects.filter(
                recipient_school=school,
                is_read=False
            ).count()
            
            context['unread_messages_count'] = unread_messages_count
            context['unread_notifications_count'] = unread_notifications_count
    
    return context

