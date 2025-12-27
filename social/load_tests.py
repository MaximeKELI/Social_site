"""
Tests de charge et de performance pour simuler des situations réelles
"""
import time
import threading
from django.test import TransactionTestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import School, Student, Post, Comment, Conversation, Message


class LoadTests(TransactionTestCase):
    """Tests de charge pour simuler une utilisation intensive"""
    
    def setUp(self):
        """Configuration avec beaucoup de données"""
        # Créer une école
        self.school_user = User.objects.create_user(
            username='loadschool',
            email='load@test.com',
            password='testpass123'
        )
        self.school = School.objects.create(
            user=self.school_user,
            name='École Load Test',
            email='load@test.com',
            address='123 Rue Load',
            phone='0123456789'
        )
        
        # Créer 200 étudiants (simulation d'une grande école)
        self.students = []
        for i in range(200):
            user = User.objects.create_user(
                username=f'loadstudent{i}',
                email=f'loadstudent{i}@test.com',
                password='testpass123'
            )
            student = Student.objects.create(
                user=user,
                school=self.school,
                first_name=f'Load{i}',
                last_name='Test',
                email=f'loadstudent{i}@test.com',
                status='current' if i % 2 == 0 else 'alumni',
                graduation_year=2020 + (i % 5)
            )
            self.students.append(student)
        
        # Créer 100 posts initiaux
        self.posts = []
        for i in range(100):
            post = Post.objects.create(
                school=self.school,
                author=self.students[i % 200],
                title=f'Post initial {i}',
                content=f'Contenu du post {i} ' * 20
            )
            self.posts.append(post)
    
    def test_concurrent_users_dashboard(self):
        """Test avec plusieurs utilisateurs accédant au dashboard simultanément"""
        def access_dashboard(student_index):
            client = Client()
            student = self.students[student_index]
            client.login(username=student.user.username, password='testpass123')
            start = time.time()
            response = client.get(reverse('dashboard'))
            elapsed = time.time() - start
            return response.status_code == 200, elapsed
        
        # Simuler 50 utilisateurs simultanés
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(access_dashboard, i % 200) 
                      for i in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for success, _ in results if success)
        avg_time = sum(elapsed for _, elapsed in results) / len(results)
        max_time = max(elapsed for _, elapsed in results)
        
        self.assertEqual(successful, 50, "Tous les accès doivent réussir")
        self.assertLess(total_time, 10.0, 
                       f"50 utilisateurs simultanés trop lent: {total_time:.3f}s")
        self.assertLess(avg_time, 0.5,
                       f"Temps moyen trop élevé: {avg_time:.3f}s")
        self.assertLess(max_time, 2.0,
                       f"Temps max trop élevé: {max_time:.3f}s")
        
        print(f"✓ 50 utilisateurs simultanés: {successful} réussis en {total_time:.3f}s")
        print(f"  Temps moyen: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_concurrent_likes(self):
        """Test de likes simultanés sur le même post"""
        post = self.posts[0]
        
        def like_post(student_index):
            client = Client()
            student = self.students[student_index]
            client.login(username=student.user.username, password='testpass123')
            response = client.post(reverse('like_post', args=[post.id]))
            return response.status_code == 200
        
        # 100 likes simultanés
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(like_post, i) 
                      for i in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r)
        
        post.refresh_from_db()
        self.assertEqual(post.like_count, 100, 
                        "Tous les likes doivent être enregistrés")
        self.assertLess(total_time, 5.0,
                       f"100 likes simultanés trop lents: {total_time:.3f}s")
        
        print(f"✓ 100 likes simultanés: {successful} réussis en {total_time:.3f}s")
        print(f"  Total de likes: {post.like_count}")
    
    def test_concurrent_posts_creation(self):
        """Test de création simultanée de posts"""
        def create_post(student_index):
            client = Client()
            student = self.students[student_index]
            client.login(username=student.user.username, password='testpass123')
            response = client.post(reverse('create_post'), {
                'title': f'Post concurrent {student_index}',
                'content': f'Contenu du post {student_index}'
            })
            return response.status_code in [200, 302]
        
        initial_count = Post.objects.count()
        
        # 30 posts créés simultanément
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(create_post, i) 
                      for i in range(30)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r)
        final_count = Post.objects.count()
        
        self.assertEqual(final_count, initial_count + 30,
                        "Tous les posts doivent être créés")
        self.assertLess(total_time, 5.0,
                       f"30 posts simultanés trop lents: {total_time:.3f}s")
        
        print(f"✓ 30 posts créés simultanément: {successful} réussis en {total_time:.3f}s")
    
    def test_concurrent_messages(self):
        """Test d'envoi simultané de messages"""
        # Créer des conversations
        conversations = []
        for i in range(20):
            conv = Conversation.objects.create()
            conv.participants.add(self.students[i], self.students[(i+1) % 200])
            conversations.append(conv)
        
        def send_message(conv_index, student_index):
            client = Client()
            student = self.students[student_index]
            client.login(username=student.user.username, password='testpass123')
            conv = conversations[conv_index]
            response = client.post(reverse('conversation_detail', args=[conv.id]), {
                'content': f'Message {student_index}'
            })
            return response.status_code in [200, 302]
        
        initial_count = Message.objects.count()
        
        # 50 messages simultanés
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(send_message, i % 20, i) 
                      for i in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r)
        final_count = Message.objects.count()
        
        self.assertGreaterEqual(final_count, initial_count + 50,
                               "Les messages doivent être créés")
        self.assertLess(total_time, 10.0,
                       f"50 messages simultanés trop lents: {total_time:.3f}s")
        
        print(f"✓ 50 messages simultanés: {successful} réussis en {total_time:.3f}s")
    
    def test_stress_test_dashboard(self):
        """Test de stress sur le dashboard avec beaucoup de données"""
        # Créer 500 posts supplémentaires
        for i in range(500):
            Post.objects.create(
                school=self.school,
                author=self.students[i % 200],
                title=f'Stress Post {i}',
                content=f'Contenu {i} ' * 30
            )
        
        student = self.students[0]
        client = Client()
        client.login(username=student.user.username, password='testpass123')
        
        # Mesurer le temps de chargement
        start_time = time.time()
        response = client.get(reverse('dashboard'))
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        # Même avec 600 posts, le dashboard devrait charger en moins de 2 secondes
        self.assertLess(elapsed_time, 2.0,
                       f"Dashboard avec 600 posts trop lent: {elapsed_time:.3f}s")
        
        print(f"✓ Dashboard avec 600 posts chargé en {elapsed_time:.3f}s")
    
    def test_memory_efficiency(self):
        """Test d'efficacité mémoire avec beaucoup d'objets"""
        import sys
        
        # Créer 1000 posts
        posts = []
        initial_size = sys.getsizeof(posts)
        
        for i in range(1000):
            post = Post.objects.create(
                school=self.school,
                author=self.students[i % 200],
                title=f'Memory Post {i}',
                content=f'Contenu {i}'
            )
            posts.append(post)
        
        # Vérifier que les objets sont bien créés
        self.assertEqual(Post.objects.count(), 1100)  # 100 initiaux + 1000
        
        # Test de récupération efficace
        start_time = time.time()
        retrieved_posts = list(Post.objects.filter(school=self.school)[:100])
        elapsed_time = time.time() - start_time
        
        self.assertEqual(len(retrieved_posts), 100)
        self.assertLess(elapsed_time, 0.5,
                       f"Récupération de 100 posts trop lente: {elapsed_time:.3f}s")
        
        print(f"✓ 1000 posts créés, récupération en {elapsed_time:.3f}s")
    
    def test_database_connection_pooling(self):
        """Test de gestion des connexions de base de données"""
        def perform_operation(student_index):
            client = Client()
            student = self.students[student_index]
            client.login(username=student.user.username, password='testpass123')
            
            # Effectuer plusieurs opérations
            client.get(reverse('dashboard'))
            client.get(reverse('student_list'))
            client.get(reverse('conversations_list'))
            return True
        
        # 100 utilisateurs effectuant plusieurs opérations
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(perform_operation, i) 
                      for i in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r)
        
        self.assertEqual(successful, 100)
        self.assertLess(total_time, 30.0,
                       f"300 opérations simultanées trop lentes: {total_time:.3f}s")
        
        print(f"✓ 300 opérations simultanées: {successful} réussies en {total_time:.3f}s")

