from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import School, Student, Post, Comment, Conversation, Message, Notification, Group, Event
from .forms import SchoolRegistrationForm, StudentRegistrationForm, PostForm, CommentForm, MessageForm


def home(request):
    """Page d'accueil"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'student_profile'):
            return redirect('dashboard')
        elif hasattr(request.user, 'school_profile'):
            return redirect('school_dashboard')
    
    schools = School.objects.filter(is_active=True)[:6]
    return render(request, 'social/home.html', {'schools': schools})


def register_school(request):
    """Inscription d'une école"""
    if request.method == 'POST':
        form = SchoolRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Inscription réussie ! Vous pouvez maintenant vous connecter.')
            return redirect('login')
    else:
        form = SchoolRegistrationForm()
    return render(request, 'social/register_school.html', {'form': form})


def register_student(request):
    """Inscription d'un étudiant"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Inscription réussie ! Vous pouvez maintenant vous connecter.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'social/register_student.html', {'form': form})


def login_view(request):
    """Vue de connexion personnalisée"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'student_profile'):
                return redirect('dashboard')
            elif hasattr(user, 'school_profile'):
                return redirect('school_dashboard')
            return redirect('home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    return render(request, 'social/login.html')


def logout_view(request):
    """Vue de déconnexion personnalisée"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')


@login_required
def dashboard(request):
    """Tableau de bord pour les étudiants"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    posts = Post.objects.filter(school=student.school).order_by('-created_at')[:20]
    
    # Récupérer les conversations de l'étudiant
    conversations = Conversation.objects.filter(participants=student).order_by('-updated_at')
    
    # Calculer le nombre de messages non lus
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
    
    context = {
        'student': student,
        'posts': posts,
        'conversations': conversations,
        'unread_messages_count': unread_messages_count,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, 'social/dashboard.html', context)


@login_required
def school_dashboard(request):
    """Tableau de bord pour les écoles"""
    if not hasattr(request.user, 'school_profile'):
        messages.error(request, 'Accès réservé aux écoles.')
        return redirect('home')
    
    school = request.user.school_profile
    students = Student.objects.filter(school=school, is_active=True)
    posts = Post.objects.filter(school=school).order_by('-created_at')[:10]
    
    context = {
        'school': school,
        'students': students,
        'posts': posts,
    }
    return render(request, 'social/school_dashboard.html', context)


@login_required
def create_post(request):
    """Créer un nouveau post"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Seuls les étudiants peuvent créer des posts.')
        return redirect('dashboard')
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.school = student.school
            post.author = student
            post.save()
            # Créer des notifications pour les étudiants de la même école (optionnel)
            # On peut limiter cela pour éviter trop de notifications
            messages.success(request, 'Post créé avec succès !')
            return redirect('dashboard')
    else:
        form = PostForm()
    
    return render(request, 'social/create_post.html', {'form': form})


@login_required
def post_detail(request, post_id):
    """Détails d'un post"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST' and hasattr(request.user, 'student_profile'):
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user.student_profile
            comment.save()
            # Créer une notification pour l'auteur du post
            if post.author != request.user.student_profile:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user.student_profile,
                    notification_type='comment',
                    title='Nouveau commentaire',
                    message=f"{request.user.student_profile.full_name} a commenté votre post: {post.title}",
                    related_post=post
                )
            messages.success(request, 'Commentaire ajouté !')
            return redirect('post_detail', post_id=post_id)
    else:
        comment_form = CommentForm()
    
    comments = Comment.objects.filter(post=post).order_by('created_at')
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'social/post_detail.html', context)


@login_required
@require_POST
def like_post(request, post_id):
    """Liker/unliker un post"""
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    post = get_object_or_404(Post, id=post_id)
    student = request.user.student_profile
    
    if post.likes.filter(id=student.id).exists():
        post.likes.remove(student)
        liked = False
    else:
        post.likes.add(student)
        liked = True
        # Créer une notification pour l'auteur du post
        if post.author != student:
            Notification.objects.create(
                recipient=post.author,
                sender=student,
                notification_type='like',
                title='Nouveau like',
                message=f"{student.full_name} a aimé votre post: {post.title}",
                related_post=post
            )
    
    return JsonResponse({'liked': liked, 'like_count': post.like_count})


@login_required
def student_list(request):
    """Liste des étudiants"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    students = Student.objects.filter(school=student.school, is_active=True).exclude(id=student.id)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'students': students,
        'search_query': search_query,
    }
    return render(request, 'social/student_list.html', context)


@login_required
def student_profile(request, student_id):
    """Profil d'un étudiant"""
    student = get_object_or_404(Student, id=student_id)
    posts = Post.objects.filter(author=student).order_by('-created_at')[:10]
    
    context = {
        'profile_student': student,
        'posts': posts,
    }
    return render(request, 'social/student_profile.html', context)


@login_required
def start_conversation(request, student_id):
    """Démarrer une conversation avec un étudiant"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    current_student = request.user.student_profile
    other_student = get_object_or_404(Student, id=student_id)
    
    # Vérifier si une conversation existe déjà
    conversation = Conversation.objects.filter(
        participants=current_student
    ).filter(
        participants=other_student
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(current_student, other_student)
    
    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):
    """Détails d'une conversation"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Vérifier que l'étudiant fait partie de la conversation
    if student not in conversation.participants.all():
        messages.error(request, 'Vous n\'avez pas accès à cette conversation.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = student
            message.save()
            conversation.save()  # Met à jour updated_at
            # Créer une notification pour les autres participants
            for participant in conversation.participants.exclude(id=student.id):
                Notification.objects.create(
                    recipient=participant,
                    sender=student,
                    notification_type='message',
                    title='Nouveau message',
                    message=f"{student.full_name} vous a envoyé un message",
                    related_message=message
                )
            return redirect('conversation_detail', conversation_id=conversation_id)
    else:
        form = MessageForm()
    
    # Marquer les messages comme lus
    Message.objects.filter(conversation=conversation).exclude(sender=student).update(is_read=True)
    
    messages_list = Message.objects.filter(conversation=conversation).order_by('created_at')
    other_participants = conversation.participants.exclude(id=student.id)
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
        'other_participants': other_participants,
    }
    return render(request, 'social/conversation_detail.html', context)


@login_required
def conversations_list(request):
    """Liste des conversations"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    conversations = Conversation.objects.filter(participants=student).order_by('-updated_at')
    
    # Ajouter le nombre de messages non lus pour chaque conversation
    for conversation in conversations:
        conversation.unread_count = Message.objects.filter(
            conversation=conversation
        ).exclude(sender=student).filter(is_read=False).count()
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'social/conversations_list.html', context)


@login_required
def group_chat(request, group_id):
    """Chat de groupe"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    group = get_object_or_404(Group, id=group_id)
    
    # Vérifier que l'étudiant est membre du groupe
    if not group.members.filter(id=student.id).exists():
        messages.error(request, 'Vous devez être membre du groupe pour accéder au chat.')
        return redirect('group_detail', group_id=group_id)
    
    # Récupérer ou créer le chat de groupe
    group_chat, created = Conversation.objects.get_or_create(
        group=group,
        is_group_chat=True,
        defaults={}
    )
    
    # S'assurer que l'étudiant est dans les participants
    if student not in group_chat.participants.all():
        group_chat.participants.add(student)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = group_chat
            message.sender = student
            message.save()
            group_chat.save()  # Met à jour updated_at
            
            # Créer des notifications pour les autres membres du groupe
            for member in group.members.exclude(id=student.id):
                Notification.objects.create(
                    recipient=member,
                    sender=student,
                    notification_type='message',
                    title='Nouveau message dans le groupe',
                    message=f"{student.full_name} a envoyé un message dans {group.name}",
                    related_message=message
                )
            
            return redirect('group_chat', group_id=group_id)
    else:
        form = MessageForm()
    
    # Marquer les messages comme lus pour cet étudiant
    Message.objects.filter(conversation=group_chat).exclude(sender=student).update(is_read=True)
    
    messages_list = Message.objects.filter(conversation=group_chat).order_by('created_at')
    
    context = {
        'group': group,
        'group_chat': group_chat,
        'messages': messages_list,
        'form': form,
    }
    return render(request, 'social/group_chat.html', context)


@login_required
def edit_profile(request):
    """Éditer le profil de l'étudiant"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        student.first_name = request.POST.get('first_name', student.first_name)
        student.last_name = request.POST.get('last_name', student.last_name)
        student.email = request.POST.get('email', student.email)
        student.phone = request.POST.get('phone', student.phone)
        student.graduation_year = request.POST.get('graduation_year') or None
        student.status = request.POST.get('status', student.status)
        student.bio = request.POST.get('bio', student.bio)
        
        if 'profile_picture' in request.FILES:
            student.profile_picture = request.FILES['profile_picture']
        
        student.save()
        messages.success(request, 'Profil mis à jour avec succès !')
        return redirect('student_profile', student_id=student.id)
    
    return render(request, 'social/edit_profile.html', {'student': student})


@login_required
@require_POST
def delete_post(request, post_id):
    """Supprimer un post"""
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    post = get_object_or_404(Post, id=post_id)
    
    if post.author != request.user.student_profile:
        return JsonResponse({'error': 'Vous ne pouvez supprimer que vos propres posts'}, status=403)
    
    post.delete()
    messages.success(request, 'Post supprimé avec succès !')
    return redirect('dashboard')


@login_required
def notifications(request):
    """Liste des notifications"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    notifications_list = Notification.objects.filter(recipient=student).order_by('-created_at')
    unread_count = notifications_list.filter(is_read=False).count()
    
    # Marquer toutes comme lues
    if request.GET.get('mark_read') == 'true':
        notifications_list.update(is_read=True)
        return redirect('notifications')
    
    context = {
        'notifications': notifications_list,
        'unread_count': unread_count,
    }
    return render(request, 'social/notifications.html', context)


@login_required
def groups_list(request):
    """Liste des groupes"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    groups = Group.objects.filter(school=student.school, is_active=True)
    
    search_query = request.GET.get('search', '')
    if search_query:
        groups = groups.filter(name__icontains=search_query)
    
    context = {
        'groups': groups,
        'search_query': search_query,
    }
    return render(request, 'social/groups_list.html', context)


@login_required
def group_detail(request, group_id):
    """Détails d'un groupe"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    group = get_object_or_404(Group, id=group_id)
    is_member = group.members.filter(id=student.id).exists()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'join':
            group.members.add(student)
            # Ajouter l'étudiant au chat de groupe s'il existe
            group_chat = Conversation.objects.filter(group=group, is_group_chat=True).first()
            if group_chat:
                group_chat.participants.add(student)
            messages.success(request, f'Vous avez rejoint le groupe {group.name} !')
        elif action == 'leave':
            group.members.remove(student)
            # Retirer l'étudiant du chat de groupe
            group_chat = Conversation.objects.filter(group=group, is_group_chat=True).first()
            if group_chat:
                group_chat.participants.remove(student)
            messages.success(request, f'Vous avez quitté le groupe {group.name}.')
        return redirect('group_detail', group_id=group_id)
    
    posts = Post.objects.filter(author__in=group.members.all(), school=group.school).order_by('-created_at')[:10]
    events = Event.objects.filter(group=group).order_by('start_date')
    group_chat = Conversation.objects.filter(group=group, is_group_chat=True).first()
    
    context = {
        'group': group,
        'is_member': is_member,
        'posts': posts,
        'events': events,
        'group_chat': group_chat,
    }
    return render(request, 'social/group_detail.html', context)


@login_required
def create_group(request):
    """Créer un nouveau groupe"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name and description:
            group = Group.objects.create(
                school=student.school,
                name=name,
                description=description,
                creator=student,
            )
            if 'image' in request.FILES:
                group.image = request.FILES['image']
            group.members.add(student)
            group.save()
            
            # Créer un chat de groupe
            group_chat = Conversation.objects.create(
                group=group,
                is_group_chat=True
            )
            group_chat.participants.add(student)
            
            # Notifier tous les étudiants de la même école
            school_students = Student.objects.filter(
                school=student.school,
                is_active=True
            ).exclude(id=student.id)
            
            for school_student in school_students:
                Notification.objects.create(
                    recipient=school_student,
                    sender=student,
                    notification_type='group',
                    title='Nouveau groupe créé',
                    message=f"{student.full_name} a créé un nouveau groupe: {group.name}",
                    related_group=group
                )
            
            messages.success(request, 'Groupe créé avec succès ! Tous les étudiants de votre école ont été notifiés.')
            return redirect('group_detail', group_id=group.id)
        else:
            messages.error(request, 'Veuillez remplir tous les champs requis.')
    
    return render(request, 'social/create_group.html')


@login_required
def events_list(request):
    """Liste des événements"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    events = Event.objects.filter(school=student.school).order_by('start_date')
    
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'upcoming':
        events = events.filter(start_date__gte=timezone.now())
    elif filter_type == 'past':
        events = events.filter(start_date__lt=timezone.now())
    
    context = {
        'events': events,
        'filter_type': filter_type,
    }
    return render(request, 'social/events_list.html', context)


@login_required
def event_detail(request, event_id):
    """Détails d'un événement"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    event = get_object_or_404(Event, id=event_id)
    is_attending = event.attendees.filter(id=student.id).exists()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'attend':
            event.attendees.add(student)
            messages.success(request, 'Vous participez maintenant à cet événement !')
        elif action == 'unattend':
            event.attendees.remove(student)
            messages.success(request, 'Vous ne participez plus à cet événement.')
        return redirect('event_detail', event_id=event_id)
    
    context = {
        'event': event,
        'is_attending': is_attending,
    }
    return render(request, 'social/event_detail.html', context)


@login_required
def create_event(request):
    """Créer un nouvel événement"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('home')
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        location = request.POST.get('location')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        group_id = request.POST.get('group')
        
        if title and description and location and start_date and end_date:
            event = Event.objects.create(
                school=student.school,
                title=title,
                description=description,
                location=location,
                start_date=start_date,
                end_date=end_date,
                organizer=student,
            )
            if group_id:
                event.group = Group.objects.get(id=group_id)
            if 'image' in request.FILES:
                event.image = request.FILES['image']
            event.save()
            messages.success(request, 'Événement créé avec succès !')
            return redirect('event_detail', event_id=event.id)
        else:
            messages.error(request, 'Veuillez remplir tous les champs requis.')
    
    groups = Group.objects.filter(school=student.school, is_active=True)
    return render(request, 'social/create_event.html', {'groups': groups})
