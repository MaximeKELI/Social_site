from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class School(models.Model):
    """Modèle pour les écoles"""
    name = models.CharField(max_length=200, verbose_name="Nom de l'école")
    email = models.EmailField(unique=True, verbose_name="Email")
    address = models.TextField(verbose_name="Adresse")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    description = models.TextField(blank=True, verbose_name="Description")
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True, verbose_name="Logo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school_profile', verbose_name="Utilisateur")
    
    class Meta:
        verbose_name = "École"
        verbose_name_plural = "Écoles"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Student(models.Model):
    """Modèle pour les étudiants"""
    GRADUATION_STATUS = [
        ('current', 'Étudiant actuel'),
        ('alumni', 'Ancien étudiant'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', verbose_name="Utilisateur")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students', verbose_name="École")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    graduation_year = models.IntegerField(null=True, blank=True, verbose_name="Année de diplôme")
    status = models.CharField(max_length=10, choices=GRADUATION_STATUS, default='current', verbose_name="Statut")
    bio = models.TextField(blank=True, verbose_name="Biographie")
    profile_picture = models.ImageField(upload_to='student_profiles/', blank=True, null=True, verbose_name="Photo de profil")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.school.name})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Conversation(models.Model):
    """Modèle pour les conversations entre étudiants et/ou écoles"""
    participants_students = models.ManyToManyField(Student, related_name='conversations', blank=True, verbose_name="Participants étudiants")
    participants_schools = models.ManyToManyField(School, related_name='conversations', blank=True, verbose_name="Participants écoles")
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='group_chat', verbose_name="Groupe")
    is_group_chat = models.BooleanField(default=False, verbose_name="Chat de groupe")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    @property
    def participants(self):
        """Retourne tous les participants (étudiants et écoles)"""
        from itertools import chain
        return list(chain(self.participants_students.all(), self.participants_schools.all()))
    
    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group_chat and self.group:
            return f"Chat du groupe: {self.group.name}"
        participants_list = ", ".join([p.full_name for p in self.participants.all()[:3]])
        return f"Conversation: {participants_list}"


class Message(models.Model):
    """Modèle pour les messages dans les conversations"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name="Conversation")
    sender_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True, verbose_name="Expéditeur étudiant")
    sender_school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True, verbose_name="Expéditeur école")
    content = models.TextField(verbose_name="Contenu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    
    @property
    def sender(self):
        """Retourne l'expéditeur (étudiant ou école)"""
        return self.sender_student or self.sender_school
    
    @property
    def sender_name(self):
        """Retourne le nom de l'expéditeur"""
        if self.sender_student:
            return self.sender_student.full_name
        elif self.sender_school:
            return self.sender_school.name
        return "Inconnu"
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message de {self.sender.full_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Post(models.Model):
    """Modèle pour les posts publics sur le mur de l'école"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='posts', verbose_name="École")
    author = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='posts', verbose_name="Auteur")
    title = models.CharField(max_length=200, verbose_name="Titre")
    content = models.TextField(verbose_name="Contenu")
    image = models.ImageField(upload_to='post_images/', blank=True, null=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    likes = models.ManyToManyField(Student, related_name='liked_posts', blank=True, verbose_name="Likes")
    
    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} par {self.author.full_name}"
    
    @property
    def like_count(self):
        return self.likes.count()


class Comment(models.Model):
    """Modèle pour les commentaires sur les posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Post")
    author = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments', verbose_name="Auteur")
    content = models.TextField(verbose_name="Contenu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.author.full_name} sur {self.post.title}"


class Notification(models.Model):
    """Modèle pour les notifications"""
    NOTIFICATION_TYPES = [
        ('like', 'Like sur un post'),
        ('comment', 'Commentaire sur un post'),
        ('message', 'Nouveau message'),
        ('post', 'Nouveau post'),
        ('group', 'Nouveau groupe'),
        ('event', 'Nouvel événement'),
    ]
    
    recipient_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True, verbose_name="Destinataire étudiant")
    recipient_school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True, verbose_name="Destinataire école")
    sender_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True, verbose_name="Expéditeur étudiant")
    sender_school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True, verbose_name="Expéditeur école")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Type")
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    related_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Post lié")
    related_message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Message lié")
    related_group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Groupe lié")
    related_event = models.ForeignKey('Event', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Événement lié")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    @property
    def recipient(self):
        """Retourne le destinataire (étudiant ou école)"""
        return self.recipient_student or self.recipient_school
    
    @property
    def sender(self):
        """Retourne l'expéditeur (étudiant ou école)"""
        return self.sender_student or self.sender_school
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification pour {self.recipient.full_name} - {self.title}"


class Group(models.Model):
    """Modèle pour les groupes/clubs d'étudiants"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='groups', verbose_name="École")
    name = models.CharField(max_length=200, verbose_name="Nom du groupe")
    description = models.TextField(verbose_name="Description")
    image = models.ImageField(upload_to='group_images/', blank=True, null=True, verbose_name="Image")
    creator_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='created_groups', null=True, blank=True, verbose_name="Créateur étudiant")
    creator_school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='created_groups', null=True, blank=True, verbose_name="Créateur école")
    members = models.ManyToManyField(Student, related_name='groups', verbose_name="Membres")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    @property
    def creator(self):
        """Retourne le créateur (étudiant ou école)"""
        return self.creator_student or self.creator_school
    
    class Meta:
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.school.name})"
    
    @property
    def member_count(self):
        return self.members.count()


class Event(models.Model):
    """Modèle pour les événements organisés par les écoles ou groupes"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='events', verbose_name="École")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='events', verbose_name="Groupe")
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    location = models.CharField(max_length=200, verbose_name="Lieu")
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(verbose_name="Date de fin")
    image = models.ImageField(upload_to='event_images/', blank=True, null=True, verbose_name="Image")
    organizer_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='organized_events', null=True, blank=True, verbose_name="Organisateur étudiant")
    organizer_school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='organized_events', null=True, blank=True, verbose_name="Organisateur école")
    attendees = models.ManyToManyField(Student, related_name='attended_events', blank=True, verbose_name="Participants")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    @property
    def organizer(self):
        """Retourne l'organisateur (étudiant ou école)"""
        return self.organizer_student or self.organizer_school
    
    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%Y-%m-%d')}"
    
    @property
    def attendee_count(self):
        return self.attendees.count()
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()
