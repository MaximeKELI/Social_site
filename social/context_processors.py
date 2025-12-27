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
    
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        
        # Calculer le nombre de messages non lus
        conversations = Conversation.objects.filter(participants=student)
        unread_messages_count = 0
        for conversation in conversations:
            unread = Message.objects.filter(
                conversation=conversation
            ).exclude(sender=student).filter(is_read=False).count()
            unread_messages_count += unread
        
        # Calculer le nombre de notifications non lues
        unread_notifications_count = Notification.objects.filter(
            recipient=student,
            is_read=False
        ).count()
        
        context['unread_messages_count'] = unread_messages_count
        context['unread_notifications_count'] = unread_notifications_count
    
    return context

