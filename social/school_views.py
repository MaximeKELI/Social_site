"""
Vues spécifiques pour les écoles
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64

from .models import (
    School, Student, Post, Comment, Conversation, Message,
    Notification, Group, Event
)


@login_required
def school_create_group(request):
    """Créer un groupe pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name and description:
            group = Group.objects.create(
                school=school,
                name=name,
                description=description,
                creator_school=school,
            )
            if 'image' in request.FILES:
                group.image = request.FILES['image']
            group.save()
            
            # Créer un chat de groupe
            group_chat = Conversation.objects.create(
                group=group,
                is_group_chat=True
            )
            group_chat.participants_schools.add(school)
            
            # Notifier tous les étudiants de l'école
            school_students = Student.objects.filter(
                school=school,
                is_active=True
            )
            
            for student in school_students:
                Notification.objects.create(
                    recipient_student=student,
                    sender_school=school,
                    notification_type='group',
                    title='Nouveau groupe créé par votre école',
                    message=f"Votre école a créé un nouveau groupe: {group.name}",
                    related_group=group
                )
            
            messages.success(request, 'Groupe créé avec succès ! Tous les étudiants ont été notifiés.')
            return redirect('school_group_detail', group_id=group.id)
        else:
            messages.error(request, 'Veuillez remplir tous les champs requis.')
    
    return render(request, 'social/school_create_group.html')


@login_required
def school_create_event(request):
    """Créer un événement pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        location = request.POST.get('location')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        group_id = request.POST.get('group')
        
        if title and description and location and start_date and end_date:
            event = Event.objects.create(
                school=school,
                title=title,
                description=description,
                location=location,
                start_date=start_date,
                end_date=end_date,
                organizer_school=school,
            )
            if group_id:
                event.group = Group.objects.get(id=group_id)
            if 'image' in request.FILES:
                event.image = request.FILES['image']
            event.save()
            
            # Notifier tous les étudiants de l'école
            school_students = Student.objects.filter(
                school=school,
                is_active=True
            )
            
            for student in school_students:
                Notification.objects.create(
                    recipient_student=student,
                    sender_school=school,
                    notification_type='event',
                    title='Nouvel événement organisé par votre école',
                    message=f"Votre école organise un événement: {event.title}",
                    related_event=event
                )
            
            messages.success(request, 'Événement créé avec succès ! Tous les étudiants ont été notifiés.')
            return redirect('school_event_detail', event_id=event.id)
        else:
            messages.error(request, 'Veuillez remplir tous les champs requis.')
    
    groups = Group.objects.filter(school=school, is_active=True)
    return render(request, 'social/school_create_event.html', {'groups': groups})


@login_required
def school_groups_list(request):
    """Liste des groupes pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    groups = Group.objects.filter(school=school, is_active=True)
    
    search_query = request.GET.get('search', '')
    if search_query:
        groups = groups.filter(name__icontains=search_query)
    
    context = {
        'groups': groups,
        'search_query': search_query,
    }
    return render(request, 'social/school_groups_list.html', context)


@login_required
def school_group_detail(request, group_id):
    """Détails d'un groupe pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    group = get_object_or_404(Group, id=group_id, school=school)
    group_chat = Conversation.objects.filter(group=group, is_group_chat=True).first()
    
    posts = Post.objects.filter(author__in=group.members.all(), school=group.school).order_by('-created_at')[:10]
    events = Event.objects.filter(group=group).order_by('start_date')
    
    context = {
        'group': group,
        'posts': posts,
        'events': events,
        'group_chat': group_chat,
    }
    return render(request, 'social/school_group_detail.html', context)


@login_required
def school_events_list(request):
    """Liste des événements pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    events = Event.objects.filter(school=school).order_by('start_date')
    
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'upcoming':
        events = events.filter(start_date__gte=timezone.now())
    elif filter_type == 'past':
        events = events.filter(start_date__lt=timezone.now())
    
    context = {
        'events': events,
        'filter_type': filter_type,
    }
    return render(request, 'social/school_events_list.html', context)


@login_required
def school_event_detail(request, event_id):
    """Détails d'un événement pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    event = get_object_or_404(Event, id=event_id, school=school)
    
    context = {
        'event': event,
    }
    return render(request, 'social/school_event_detail.html', context)


@login_required
def school_conversations_list(request):
    """Liste des conversations pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    conversations = Conversation.objects.filter(participants_schools=school).order_by('-updated_at')
    
    # Calculer les messages non lus
    for conversation in conversations:
        conversation.unread_count = Message.objects.filter(
            conversation=conversation
        ).exclude(sender_school=school).filter(is_read=False).count()
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'social/school_conversations_list.html', context)


@login_required
def school_conversation_detail(request, conversation_id):
    """Détails d'une conversation pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Vérifier que l'école fait partie de la conversation
    if school not in conversation.participants_schools.all():
        messages.error(request, 'Vous n\'avez pas accès à cette conversation.')
        return redirect('school_dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender_school=school,
                content=content
            )
            conversation.save()  # Met à jour updated_at
            
            # Créer des notifications pour les autres participants
            for student in conversation.participants_students.all():
                Notification.objects.create(
                    recipient_student=student,
                    sender_school=school,
                    notification_type='message',
                    title='Nouveau message de votre école',
                    message=f"{school.name} vous a envoyé un message",
                    related_message=message
                )
            
            return redirect('school_conversation_detail', conversation_id=conversation_id)
    
    # Marquer les messages comme lus
    Message.objects.filter(conversation=conversation).exclude(sender_school=school).update(is_read=True)
    
    messages_list = Message.objects.filter(conversation=conversation).order_by('created_at')
    other_participants = conversation.participants_students.all()
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_participants': other_participants,
    }
    return render(request, 'social/school_conversation_detail.html', context)


@login_required
def school_start_conversation(request, student_id):
    """Démarrer une conversation avec un étudiant"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    student = get_object_or_404(Student, id=student_id, school=school)
    
    # Vérifier si une conversation existe déjà
    conversation = Conversation.objects.filter(
        participants_schools=school
    ).filter(
        participants_students=student
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants_schools.add(school)
        conversation.participants_students.add(student)
    
    return redirect('school_conversation_detail', conversation_id=conversation.id)


@login_required
def school_notifications(request):
    """Liste des notifications pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    notifications_list = Notification.objects.filter(recipient_school=school).order_by('-created_at')
    unread_count = notifications_list.filter(is_read=False).count()
    
    # Marquer toutes comme lues
    if request.GET.get('mark_read') == 'true':
        notifications_list.update(is_read=True)
        return redirect('school_notifications')
    
    context = {
        'notifications': notifications_list,
        'unread_count': unread_count,
    }
    return render(request, 'social/school_notifications.html', context)


@login_required
def school_statistics(request):
    """Statistiques détaillées pour une école"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    
    # Statistiques de base
    total_students = Student.objects.filter(school=school, is_active=True).count()
    current_students = Student.objects.filter(school=school, status='current', is_active=True).count()
    alumni_students = Student.objects.filter(school=school, status='alumni', is_active=True).count()
    total_posts = Post.objects.filter(school=school).count()
    total_groups = Group.objects.filter(school=school, is_active=True).count()
    total_events = Event.objects.filter(school=school).count()
    total_messages = Message.objects.filter(conversation__participants_schools=school).count()
    
    # Statistiques par mois (posts) - SQLite
    from django.db import connection
    if 'sqlite' in connection.vendor:
        posts_by_month = Post.objects.filter(school=school).extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(count=Count('id')).order_by('month')
    else:
        # Pour PostgreSQL
        posts_by_month = Post.objects.filter(school=school).extra(
            select={'month': "to_char(created_at, 'YYYY-MM')"}
        ).values('month').annotate(count=Count('id')).order_by('month')
    
    # Statistiques par statut d'étudiant
    students_by_status = Student.objects.filter(school=school, is_active=True).values('status').annotate(count=Count('id'))
    
    # Statistiques par année de diplôme
    students_by_year = Student.objects.filter(
        school=school,
        is_active=True,
        graduation_year__isnull=False
    ).values('graduation_year').annotate(count=Count('id')).order_by('graduation_year')
    
    # Activité récente (7 derniers jours)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_posts = Post.objects.filter(school=school, created_at__gte=seven_days_ago).count()
    recent_messages = Message.objects.filter(
        conversation__participants_schools=school,
        created_at__gte=seven_days_ago
    ).count()
    
    context = {
        'school': school,
        'total_students': total_students,
        'current_students': current_students,
        'alumni_students': alumni_students,
        'total_posts': total_posts,
        'total_groups': total_groups,
        'total_events': total_events,
        'total_messages': total_messages,
        'posts_by_month': posts_by_month,
        'students_by_status': students_by_status,
        'students_by_year': students_by_year,
        'recent_posts': recent_posts,
        'recent_messages': recent_messages,
    }
    return render(request, 'social/school_statistics.html', context)


@login_required
def school_statistics_chart(request, chart_type):
    """Générer un graphique pour les statistiques"""
    if not hasattr(request.user, 'school_profile'):
        return HttpResponse('Unauthorized', status=403)
    
    school = request.user.school_profile
    
    plt.figure(figsize=(10, 6))
    
    if chart_type == 'posts_by_month':
        from django.db import connection
        if 'sqlite' in connection.vendor:
            posts = Post.objects.filter(school=school).extra(
                select={'month': "strftime('%%Y-%%m', created_at)"}
            ).values('month').annotate(count=Count('id')).order_by('month')
        else:
            posts = Post.objects.filter(school=school).extra(
                select={'month': "to_char(created_at, 'YYYY-MM')"}
            ).values('month').annotate(count=Count('id')).order_by('month')
        
        months = [p['month'] for p in posts]
        counts = [p['count'] for p in posts]
        
        plt.bar(months, counts)
        plt.title('Posts par mois')
        plt.xlabel('Mois')
        plt.ylabel('Nombre de posts')
        plt.xticks(rotation=45)
        
    elif chart_type == 'students_by_status':
        students = Student.objects.filter(school=school, is_active=True).values('status').annotate(count=Count('id'))
        
        labels = [s['status'] for s in students]
        sizes = [s['count'] for s in students]
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        plt.title('Répartition des étudiants par statut')
        
    elif chart_type == 'students_by_year':
        students = Student.objects.filter(
            school=school,
            is_active=True,
            graduation_year__isnull=False
        ).values('graduation_year').annotate(count=Count('id')).order_by('graduation_year')
        
        years = [str(s['graduation_year']) for s in students]
        counts = [s['count'] for s in students]
        
        plt.bar(years, counts)
        plt.title('Étudiants par année de diplôme')
        plt.xlabel('Année')
        plt.ylabel('Nombre d\'étudiants')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Convertir en image base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(image_png, content_type='image/png')
    return response


@login_required
def school_export_csv(request):
    """Exporter les données en CSV"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="statistiques_{school.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # En-têtes
    writer.writerow(['Type', 'Donnée', 'Valeur'])
    
    # Statistiques générales
    writer.writerow(['Étudiants', 'Total', Student.objects.filter(school=school, is_active=True).count()])
    writer.writerow(['Étudiants', 'Actuels', Student.objects.filter(school=school, status='current', is_active=True).count()])
    writer.writerow(['Étudiants', 'Anciens', Student.objects.filter(school=school, status='alumni', is_active=True).count()])
    writer.writerow(['Posts', 'Total', Post.objects.filter(school=school).count()])
    writer.writerow(['Groupes', 'Total', Group.objects.filter(school=school, is_active=True).count()])
    writer.writerow(['Événements', 'Total', Event.objects.filter(school=school).count()])
    
    # Détails des étudiants
    writer.writerow([])
    writer.writerow(['Détails des étudiants'])
    writer.writerow(['Prénom', 'Nom', 'Email', 'Statut', 'Année de diplôme'])
    for student in Student.objects.filter(school=school, is_active=True):
        writer.writerow([
            student.first_name,
            student.last_name,
            student.email,
            student.get_status_display(),
            student.graduation_year or ''
        ])
    
    return response


@login_required
def school_export_pdf(request):
    """Exporter les statistiques en PDF"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Titre
    title = Paragraph(f"Statistiques - {school.name}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Statistiques générales
    elements.append(Paragraph("Statistiques Générales", styles['Heading2']))
    
    data = [
        ['Métrique', 'Valeur'],
        ['Total étudiants', str(Student.objects.filter(school=school, is_active=True).count())],
        ['Étudiants actuels', str(Student.objects.filter(school=school, status='current', is_active=True).count())],
        ['Anciens étudiants', str(Student.objects.filter(school=school, status='alumni', is_active=True).count())],
        ['Total posts', str(Post.objects.filter(school=school).count())],
        ['Total groupes', str(Group.objects.filter(school=school, is_active=True).count())],
        ['Total événements', str(Event.objects.filter(school=school).count())],
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Liste des étudiants
    elements.append(Paragraph("Liste des Étudiants", styles['Heading2']))
    
    student_data = [['Prénom', 'Nom', 'Email', 'Statut']]
    for student in Student.objects.filter(school=school, is_active=True)[:50]:  # Limiter à 50
        student_data.append([
            student.first_name,
            student.last_name,
            student.email,
            student.get_status_display()
        ])
    
    student_table = Table(student_data)
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(student_table)
    
    # Date de génération
    elements.append(Spacer(1, 12))
    date_text = f"Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}"
    elements.append(Paragraph(date_text, styles['Normal']))
    
    # Construire le PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="statistiques_{school.name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response

