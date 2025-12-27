import time
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
import io

from .models import (
    School, Student, Post, Comment, Conversation, Message,
    Notification, Group, Event
)


class ModelTests(TestCase):
    """Tests unitaires pour les modèles"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        # Créer un utilisateur école
        self.school_user = User.objects.create_user(
            username='school1',
            email='school1@test.com',
            password='testpass123'
        )
        self.school = School.objects.create(
            user=self.school_user,
            name='École Test',
            email='school1@test.com',
            address='123 Rue Test',
            phone='0123456789',
            description='Une école de test'
        )
        
        # Créer des utilisateurs étudiants
        self.student_user1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123'
        )
        self.student1 = Student.objects.create(
            user=self.student_user1,
            school=self.school,
            first_name='Jean',
            last_name='Dupont',
            email='student1@test.com',
            status='current',
            graduation_year=2024
        )
        
        self.student_user2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123'
        )
        self.student2 = Student.objects.create(
            user=self.student_user2,
            school=self.school,
            first_name='Marie',
            last_name='Martin',
            email='student2@test.com',
            status='alumni',
            graduation_year=2020
        )
    
    def test_school_creation(self):
        """Test de création d'une école"""
        self.assertEqual(self.school.name, 'École Test')
        self.assertEqual(self.school.email, 'school1@test.com')
        self.assertTrue(self.school.is_active)
        self.assertEqual(str(self.school), 'École Test')
    
    def test_student_creation(self):
        """Test de création d'un étudiant"""
        self.assertEqual(self.student1.full_name, 'Jean Dupont')
        self.assertEqual(self.student1.school, self.school)
        self.assertEqual(self.student1.status, 'current')
        self.assertEqual(str(self.student1), 'Jean Dupont (École Test)')
    
    def test_post_creation(self):
        """Test de création d'un post"""
        post = Post.objects.create(
            school=self.school,
            author=self.student1,
            title='Mon premier post',
            content='Contenu du post de test'
        )
        self.assertEqual(post.title, 'Mon premier post')
        self.assertEqual(post.author, self.student1)
        self.assertEqual(post.like_count, 0)
    
    def test_post_likes(self):
        """Test du système de likes"""
        post = Post.objects.create(
            school=self.school,
            author=self.student1,
            title='Post avec likes',
            content='Contenu'
        )
        post.likes.add(self.student2)
        self.assertEqual(post.like_count, 1)
        self.assertTrue(self.student2 in post.likes.all())
    
    def test_comment_creation(self):
        """Test de création d'un commentaire"""
        post = Post.objects.create(
            school=self.school,
            author=self.student1,
            title='Post',
            content='Contenu'
        )
        comment = Comment.objects.create(
            post=post,
            author=self.student2,
            content='Super post !'
        )
        self.assertEqual(comment.content, 'Super post !')
        self.assertEqual(comment.post, post)
    
    def test_conversation_creation(self):
        """Test de création d'une conversation"""
        conversation = Conversation.objects.create()
        conversation.participants_students.add(self.student1, self.student2)
        self.assertEqual(conversation.participants_students.count(), 2)
    
    def test_message_creation(self):
        """Test de création d'un message"""
        conversation = Conversation.objects.create()
        conversation.participants_students.add(self.student1, self.student2)
        message = Message.objects.create(
            conversation=conversation,
            sender_student=self.student1,
            content='Bonjour !'
        )
        self.assertEqual(message.content, 'Bonjour !')
        self.assertFalse(message.is_read)
    
    def test_notification_creation(self):
        """Test de création d'une notification"""
        post = Post.objects.create(
            school=self.school,
            author=self.student1,
            title='Post',
            content='Contenu'
        )
        notification = Notification.objects.create(
            recipient_student=self.student1,
            sender_student=self.student2,
            notification_type='like',
            title='Nouveau like',
            message='Marie Martin a aimé votre post',
            related_post=post
        )
        self.assertEqual(notification.recipient_student, self.student1)
        self.assertFalse(notification.is_read)
    
    def test_group_creation(self):
        """Test de création d'un groupe"""
        group = Group.objects.create(
            school=self.school,
            name='Groupe Test',
            description='Description du groupe',
            creator_student=self.student1
        )
        group.members.add(self.student1, self.student2)
        self.assertEqual(group.name, 'Groupe Test')
        self.assertEqual(group.member_count, 2)
    
    def test_event_creation(self):
        """Test de création d'un événement"""
        event = Event.objects.create(
            school=self.school,
            title='Événement Test',
            description='Description',
            location='Lieu test',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=7, hours=2),
            organizer_student=self.student1
        )
        event.attendees.add(self.student1, self.student2)
        self.assertEqual(event.title, 'Événement Test')
        self.assertEqual(event.attendee_count, 2)
        self.assertTrue(event.is_upcoming)


class ViewTests(TestCase):
    """Tests unitaires pour les vues"""
    
    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        
        # Créer une école
        self.school_user = User.objects.create_user(
            username='school1',
            email='school1@test.com',
            password='testpass123'
        )
        self.school = School.objects.create(
            user=self.school_user,
            name='École Test',
            email='school1@test.com',
            address='123 Rue Test',
            phone='0123456789'
        )
        
        # Créer un étudiant
        self.student_user = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            school=self.school,
            first_name='Jean',
            last_name='Dupont',
            email='student1@test.com',
            status='current'
        )
    
    def test_home_page(self):
        """Test de la page d'accueil"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'School Social')
    
    def test_login_page(self):
        """Test de la page de connexion"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connexion')
    
    def test_login_success(self):
        """Test de connexion réussie"""
        response = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertIn('dashboard', response.url)
    
    def test_login_failure(self):
        """Test de connexion échouée"""
        response = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incorrect')
    
    def test_dashboard_requires_login(self):
        """Test que le dashboard nécessite une connexion"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_dashboard_authenticated(self):
        """Test du dashboard pour un utilisateur connecté"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tableau de bord')
    
    def test_create_post(self):
        """Test de création d'un post"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('create_post'), {
            'title': 'Nouveau post',
            'content': 'Contenu du post'
        })
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertTrue(Post.objects.filter(title='Nouveau post').exists())
    
    def test_like_post(self):
        """Test de like d'un post"""
        post = Post.objects.create(
            school=self.school,
            author=self.student,
            title='Post à liker',
            content='Contenu'
        )
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('like_post', args=[post.id]))
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)
    
    def test_student_list(self):
        """Test de la liste des étudiants"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Liste des étudiants')
    
    def test_logout(self):
        """Test de déconnexion"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirection
        # La redirection peut être vers '/' ou vers 'home'
        self.assertTrue(response.url == '/' or 'home' in response.url)


class PerformanceTests(TransactionTestCase):
    """Tests de performance en situations réelles"""
    
    def setUp(self):
        """Configuration avec beaucoup de données"""
        self.client = Client()
        
        # Créer une école
        self.school_user = User.objects.create_user(
            username='school1',
            email='school1@test.com',
            password='testpass123'
        )
        self.school = School.objects.create(
            user=self.school_user,
            name='École Performance Test',
            email='school1@test.com',
            address='123 Rue Test',
            phone='0123456789'
        )
        
        # Créer 100 étudiants (simulation d'une école réelle)
        self.students = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'student{i}',
                email=f'student{i}@test.com',
                password='testpass123'
            )
            student = Student.objects.create(
                user=user,
                school=self.school,
                first_name=f'Prénom{i}',
                last_name=f'Nom{i}',
                email=f'student{i}@test.com',
                status='current' if i % 2 == 0 else 'alumni',
                graduation_year=2020 + (i % 5)
            )
            self.students.append(student)
        
        # Créer 50 posts (simulation d'activité)
        self.posts = []
        for i in range(50):
            post = Post.objects.create(
                school=self.school,
                author=self.students[i % 100],
                title=f'Post {i}',
                content=f'Contenu du post {i} ' * 10  # Contenu plus long
            )
            # Ajouter des likes aléatoires
            for j in range(i % 20):  # Jusqu'à 19 likes par post
                post.likes.add(self.students[j % 100])
            self.posts.append(post)
        
        # Créer 200 commentaires
        for i in range(200):
            Comment.objects.create(
                post=self.posts[i % 50],
                author=self.students[i % 100],
                content=f'Commentaire {i}'
            )
    
    def test_dashboard_performance(self):
        """Test de performance du dashboard avec beaucoup de données"""
        self.client.login(username='student0', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('dashboard'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        elapsed_time = end_time - start_time
        
        # Le dashboard devrait charger en moins de 1 seconde
        self.assertLess(elapsed_time, 1.0, 
                       f"Dashboard trop lent: {elapsed_time:.3f}s")
        print(f"✓ Dashboard chargé en {elapsed_time:.3f}s avec 50 posts")
    
    def test_student_list_performance(self):
        """Test de performance de la liste des étudiants"""
        self.client.login(username='student0', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('student_list'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        elapsed_time = end_time - start_time
        
        # La liste devrait charger en moins de 0.5 secondes
        self.assertLess(elapsed_time, 0.5,
                       f"Liste étudiants trop lente: {elapsed_time:.3f}s")
        print(f"✓ Liste de 100 étudiants chargée en {elapsed_time:.3f}s")
    
    def test_post_detail_performance(self):
        """Test de performance de la page de détail d'un post"""
        self.client.login(username='student0', password='testpass123')
        post = self.posts[0]
        
        start_time = time.time()
        response = self.client.get(reverse('post_detail', args=[post.id]))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        elapsed_time = end_time - start_time
        
        self.assertLess(elapsed_time, 0.3,
                       f"Page post trop lente: {elapsed_time:.3f}s")
        print(f"✓ Page post chargée en {elapsed_time:.3f}s")
    
    def test_concurrent_likes(self):
        """Test de performance avec beaucoup de likes simultanés"""
        post = self.posts[0]
        self.client.login(username='student0', password='testpass123')
        
        start_time = time.time()
        # Simuler 50 likes rapides
        for i in range(50):
            self.client.post(reverse('like_post', args=[post.id]))
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        post.refresh_from_db()
        
        # Les likes devraient être traités rapidement
        self.assertLess(elapsed_time, 2.0,
                       f"Likes trop lents: {elapsed_time:.3f}s")
        print(f"✓ 50 likes traités en {elapsed_time:.3f}s")
    
    def test_search_performance(self):
        """Test de performance de la recherche"""
        self.client.login(username='student0', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('student_list'), {'search': 'Prénom'})
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        elapsed_time = end_time - start_time
        
        self.assertLess(elapsed_time, 0.5,
                       f"Recherche trop lente: {elapsed_time:.3f}s")
        print(f"✓ Recherche effectuée en {elapsed_time:.3f}s")
    
    def test_mass_notification_creation(self):
        """Test de création massive de notifications"""
        post = self.posts[0]
        
        start_time = time.time()
        # Créer 100 notifications
        notifications = []
        for i in range(100):
            notification = Notification.objects.create(
                recipient=self.students[i],
                sender=self.students[(i+1) % 100],
                notification_type='like',
                title='Nouveau like',
                message=f'Notification {i}',
                related_post=post
            )
            notifications.append(notification)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertEqual(Notification.objects.count(), 100)
        
        self.assertLess(elapsed_time, 1.0,
                       f"Création notifications trop lente: {elapsed_time:.3f}s")
        print(f"✓ 100 notifications créées en {elapsed_time:.3f}s")
    
    def test_conversation_performance(self):
        """Test de performance des conversations"""
        # Créer 20 conversations
        conversations = []
        for i in range(20):
            conv = Conversation.objects.create()
            conv.participants_students.add(self.students[i], self.students[(i+1) % 100])
            conversations.append(conv)
        
        # Créer 100 messages
        start_time = time.time()
        for i in range(100):
            Message.objects.create(
                conversation=conversations[i % 20],
                sender=self.students[i % 100],
                content=f'Message {i}'
            )
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertEqual(Message.objects.count(), 100)
        
        self.assertLess(elapsed_time, 1.0,
                       f"Création messages trop lente: {elapsed_time:.3f}s")
        print(f"✓ 100 messages créés en {elapsed_time:.3f}s")
    
    def test_bulk_operations(self):
        """Test d'opérations en masse"""
        # Test de création en masse de posts
        start_time = time.time()
        new_posts = []
        for i in range(100):
            post = Post(
                school=self.school,
                author=self.students[i % 100],
                title=f'Bulk Post {i}',
                content=f'Contenu {i}'
            )
            new_posts.append(post)
        Post.objects.bulk_create(new_posts)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertEqual(Post.objects.count(), 150)  # 50 + 100
        
        self.assertLess(elapsed_time, 2.0,
                       f"Bulk create trop lent: {elapsed_time:.3f}s")
        print(f"✓ 100 posts créés en masse en {elapsed_time:.3f}s")


class RealWorldScenarioTests(TransactionTestCase):
    """Tests de scénarios réels d'utilisation"""
    
    def setUp(self):
        """Simulation d'un scénario réel"""
        self.client = Client()
        
        # Créer une école
        school_user = User.objects.create_user(
            username='realschool',
            email='school@real.com',
            password='testpass123'
        )
        self.school = School.objects.create(
            user=school_user,
            name='École Réelle',
            email='school@real.com',
            address='123 Rue Réelle',
            phone='0123456789'
        )
        
        # Créer 30 étudiants (classe moyenne)
        self.students = []
        for i in range(30):
            user = User.objects.create_user(
                username=f'realstudent{i}',
                email=f'student{i}@real.com',
                password='testpass123'
            )
            student = Student.objects.create(
                user=user,
                school=self.school,
                first_name=f'Étudiant{i}',
                last_name='Réel',
                email=f'student{i}@real.com',
                status='current' if i < 20 else 'alumni',
                graduation_year=2020 + (i % 4)
            )
            self.students.append(student)
    
    def test_complete_user_journey(self):
        """Test d'un parcours utilisateur complet"""
        # 1. Inscription
        response = self.client.post(reverse('register_student'), {
            'username': 'newstudent',
            'email': 'new@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
            'first_name': 'Nouveau',
            'last_name': 'Étudiant',
            'school': self.school.id,
            'status': 'current'
        })
        self.assertEqual(response.status_code, 200)
        
        # 2. Connexion
        response = self.client.post(reverse('login'), {
            'username': 'newstudent',
            'password': 'complexpass123'
        })
        self.assertEqual(response.status_code, 302)
        
        # 3. Accès au dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # 4. Création d'un post
        response = self.client.post(reverse('create_post'), {
            'title': 'Mon premier post',
            'content': 'Salut tout le monde !'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(title='Mon premier post').exists())
        
        # 5. Voir la liste des étudiants
        response = self.client.get(reverse('student_list'))
        self.assertEqual(response.status_code, 200)
        
        # 6. Démarrer une conversation
        other_student = self.students[0]
        response = self.client.get(reverse('start_conversation', 
                                         args=[other_student.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Conversation.objects.exists())
        
        print("✓ Parcours utilisateur complet réussi")
    
    def test_social_interaction_scenario(self):
        """Test d'un scénario d'interaction sociale"""
        student1 = self.students[0]
        student2 = self.students[1]
        
        # Étudiant 1 se connecte
        self.client.login(username=student1.user.username, password='testpass123')
        
        # Étudiant 1 crée un post
        post = Post.objects.create(
            school=self.school,
            author=student1,
            title='Post intéressant',
            content='Regardez ce post !'
        )
        
        # Étudiant 2 se connecte
        self.client.logout()
        self.client.login(username=student2.user.username, password='testpass123')
        
        # Étudiant 2 like le post
        response = self.client.post(reverse('like_post', args=[post.id]))
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)
        
        # Étudiant 2 commente
        response = self.client.post(reverse('post_detail', args=[post.id]), {
            'content': 'Super post !'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(post=post).exists())
        
        # Vérifier les notifications
        notifications = Notification.objects.filter(recipient=student1)
        self.assertTrue(notifications.exists())
        
        print("✓ Scénario d'interaction sociale réussi")
    
    def test_group_activity_scenario(self):
        """Test d'un scénario d'activité de groupe"""
        student = self.students[0]
        self.client.login(username=student.user.username, password='testpass123')
        
        # Créer un groupe
        group = Group.objects.create(
            school=self.school,
            name='Groupe de Test',
            description='Description',
            creator=student
        )
        group.members.add(student)
        
        # Créer un événement pour le groupe
        event = Event.objects.create(
            school=self.school,
            group=group,
            title='Événement du groupe',
            description='Description',
            location='Lieu',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=7, hours=2),
            organizer=student
        )
        
        # Ajouter des participants
        for i in range(10):
            event.attendees.add(self.students[i])
        
        self.assertEqual(event.attendee_count, 10)
        self.assertEqual(group.member_count, 1)
        
        print("✓ Scénario d'activité de groupe réussi")


class DatabaseQueryTests(TestCase):
    """Tests d'optimisation des requêtes de base de données"""
    
    def setUp(self):
        """Configuration avec données"""
        self.school_user = User.objects.create_user(
            username='school1',
            email='school1@test.com',
            password='testpass123'
        )
        self.school = School.objects.create(
            user=self.school_user,
            name='École Test',
            email='school1@test.com',
            address='123 Rue Test',
            phone='0123456789'
        )
        
        # Créer 20 étudiants
        self.students = []
        for i in range(20):
            user = User.objects.create_user(
                username=f'student{i}',
                email=f'student{i}@test.com',
                password='testpass123'
            )
            student = Student.objects.create(
                user=user,
                school=self.school,
                first_name=f'Prénom{i}',
                last_name=f'Nom{i}',
                email=f'student{i}@test.com',
                status='current'
            )
            self.students.append(student)
        
        # Créer 10 posts avec commentaires
        for i in range(10):
            post = Post.objects.create(
                school=self.school,
                author=self.students[i],
                title=f'Post {i}',
                content='Contenu'
            )
            # Ajouter des commentaires
            for j in range(5):
                Comment.objects.create(
                    post=post,
                    author=self.students[j],
                    content=f'Commentaire {j}'
                )
    
    def test_query_optimization_dashboard(self):
        """Test d'optimisation des requêtes pour le dashboard"""
        from django.db import reset_queries, connection
        
        student = self.students[0]
        self.client = Client()
        self.client.login(username=student.user.username, password='testpass123')
        
        # Compter les requêtes
        reset_queries()
        response = self.client.get(reverse('dashboard'))
        query_count = len(connection.queries)
        
        self.assertEqual(response.status_code, 200)
        # Vérifier qu'on a moins de 15 requêtes (marge de sécurité)
        self.assertLess(query_count, 15, 
                       f"Trop de requêtes: {query_count}")
        
        print(f"✓ Dashboard optimisé ({query_count} requêtes)")
    
    def test_query_optimization_post_detail(self):
        """Test d'optimisation pour la page de détail d'un post"""
        from django.db import reset_queries, connection
        
        post = Post.objects.first()
        student = self.students[0]
        self.client = Client()
        self.client.login(username=student.user.username, password='testpass123')
        
        # Compter les requêtes
        reset_queries()
        response = self.client.get(reverse('post_detail', args=[post.id]))
        query_count = len(connection.queries)
        
        self.assertEqual(response.status_code, 200)
        # Moins de 10 requêtes pour charger un post avec ses commentaires
        self.assertLess(query_count, 10, 
                       f"Trop de requêtes: {query_count}")
        
        print(f"✓ Page post optimisée ({query_count} requêtes)")
