from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import School, Student, Post, Comment, Conversation, Message
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
    
    context = {
        'student': student,
        'posts': posts,
        'conversations': conversations,
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
