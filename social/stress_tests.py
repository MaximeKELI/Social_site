"""
Tests de stress extrêmes - 1000 utilisateurs simultanés
Simulation de conditions de production réelles
"""
import time
import statistics
from django.test import TransactionTestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from .models import School, Student, Post, Comment, Conversation, Message, Group, Event


class ExtremeLoadTests(TransactionTestCase):
    """Tests de charge extrême avec 1000 utilisateurs simultanés"""
    
    def setUp(self):
        """Configuration avec beaucoup de données"""
        print("\n🔧 Configuration des tests de stress...")
        
        # Créer une école
        self.school_user = User.objects.create_user(
            username='stressschool',
            email='stress@test.com',
            password='testpass123'
        )
        self.school = School.objects.create(
            user=self.school_user,
            name='École Stress Test',
            email='stress@test.com',
            address='123 Rue Stress',
            phone='0123456789'
        )
        
        # Créer 1000 étudiants
        print("📝 Création de 1000 étudiants...")
        self.students = []
        for i in range(1000):
            user = User.objects.create_user(
                username=f'stressstudent{i}',
                email=f'stressstudent{i}@test.com',
                password='testpass123'
            )
            student = Student.objects.create(
                user=user,
                school=self.school,
                first_name=f'Stress{i}',
                last_name='Test',
                email=f'stressstudent{i}@test.com',
                status='current' if i % 2 == 0 else 'alumni',
                graduation_year=2020 + (i % 5)
            )
            self.students.append(student)
        
        # Créer 100 écoles
        print("📝 Création de 100 écoles...")
        self.schools = []
        for i in range(100):
            school_user = User.objects.create_user(
                username=f'stressschool{i}',
                email=f'stressschool{i}@test.com',
                password='testpass123'
            )
            school = School.objects.create(
                user=school_user,
                name=f'École Stress {i}',
                email=f'stressschool{i}@test.com',
                address=f'Adresse {i}',
                phone=f'012345678{i}'
            )
            self.schools.append(school)
        
        # Créer 500 posts initiaux
        print("📝 Création de 500 posts...")
        self.posts = []
        for i in range(500):
            post = Post.objects.create(
                school=self.school,
                author=self.students[i % 1000],
                title=f'Post initial {i}',
                content=f'Contenu du post {i} ' * 50
            )
            self.posts.append(post)
        
        # Créer 50 groupes
        print("📝 Création de 50 groupes...")
        self.groups = []
        for i in range(50):
            group = Group.objects.create(
                school=self.school,
                name=f'Groupe Stress {i}',
                description=f'Description du groupe {i}',
                creator=self.students[i % 1000]
            )
            # Ajouter 20 membres par groupe
            group.members.add(*self.students[i*20:(i+1)*20])
            self.groups.append(group)
        
        print("✅ Configuration terminée\n")
    
    def test_1000_students_dashboard_simultaneous(self):
        """1000 étudiants accédant au dashboard simultanément"""
        print("\n🚀 Test: 1000 étudiants → Dashboard simultané")
        
        results = []
        lock = Lock()
        
        def access_dashboard(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                response = client.get(reverse('dashboard'))
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code == 200,
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code == 200, elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(access_dashboard, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            max_time = max(times)
            min_time = min(times)
        else:
            avg_time = median_time = max_time = min_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps médian: {median_time:.3f}s")
        print(f"  📊 Temps min: {min_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        # Vérifications
        self.assertGreater(successful, 950, 
                          f"Trop d'échecs: {1000-successful} échecs sur 1000")
        self.assertLess(total_time, 60.0,
                       f"Trop lent: {total_time:.2f}s pour 1000 requêtes")
        self.assertLess(avg_time, 2.0,
                       f"Temps moyen trop élevé: {avg_time:.3f}s")
    
    def test_1000_students_create_posts_simultaneous(self):
        """1000 étudiants créant des posts simultanément"""
        print("\n🚀 Test: 1000 étudiants → Création de posts simultanée")
        
        initial_count = Post.objects.count()
        results = []
        lock = Lock()
        
        def create_post(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                response = client.post(reverse('create_post'), {
                    'title': f'Post simultané {student_index}',
                    'content': f'Contenu du post {student_index}'
                })
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code in [200, 302],
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code in [200, 302], elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(create_post, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        final_count = Post.objects.count()
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  📝 Posts créés: {final_count - initial_count}")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 950)
        self.assertGreaterEqual(final_count, initial_count + 950)
        self.assertLess(total_time, 120.0)
    
    def test_1000_students_likes_simultaneous(self):
        """1000 étudiants likant simultanément"""
        print("\n🚀 Test: 1000 étudiants → Likes simultanés")
        
        post = self.posts[0]
        results = []
        lock = Lock()
        
        def like_post(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                response = client.post(reverse('like_post', args=[post.id]))
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code == 200,
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code == 200, elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(like_post, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        
        post.refresh_from_db()
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  ❤️  Total de likes: {post.like_count}")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 950)
        self.assertGreaterEqual(post.like_count, 950)
        self.assertLess(total_time, 60.0)
    
    def test_1000_students_comments_simultaneous(self):
        """1000 étudiants commentant simultanément"""
        print("\n🚀 Test: 1000 étudiants → Commentaires simultanés")
        
        post = self.posts[0]
        initial_count = Comment.objects.count()
        results = []
        lock = Lock()
        
        def create_comment(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                response = client.post(reverse('post_detail', args=[post.id]), {
                    'content': f'Commentaire {student_index}'
                })
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code in [200, 302],
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code in [200, 302], elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(create_comment, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        final_count = Comment.objects.count()
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  💬 Commentaires créés: {final_count - initial_count}")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 950)
        self.assertGreaterEqual(final_count, initial_count + 950)
        self.assertLess(total_time, 120.0)
    
    def test_1000_students_messages_simultaneous(self):
        """1000 étudiants envoyant des messages simultanément"""
        print("\n🚀 Test: 1000 étudiants → Messages simultanés")
        
        # Créer 100 conversations
        conversations = []
        for i in range(100):
            conv = Conversation.objects.create()
            conv.participants.add(self.students[i], self.students[(i+1) % 1000])
            conversations.append(conv)
        
        initial_count = Message.objects.count()
        results = []
        lock = Lock()
        
        def send_message(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                conv = conversations[student_index % 100]
                start = time.time()
                response = client.post(reverse('conversation_detail', args=[conv.id]), {
                    'content': f'Message {student_index}'
                })
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code in [200, 302],
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code in [200, 302], elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(send_message, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        final_count = Message.objects.count()
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  💌 Messages créés: {final_count - initial_count}")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 950)
        self.assertGreaterEqual(final_count, initial_count + 950)
        self.assertLess(total_time, 120.0)
    
    def test_1000_students_search_simultaneous(self):
        """1000 étudiants recherchant simultanément"""
        print("\n🚀 Test: 1000 étudiants → Recherche simultanée")
        
        results = []
        lock = Lock()
        
        def search_students(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                response = client.get(reverse('student_list'), {
                    'search': f'Stress{student_index % 100}'
                })
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code == 200,
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code == 200, elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(search_students, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 950)
        self.assertLess(total_time, 60.0)
    
    def test_1000_schools_dashboard_simultaneous(self):
        """1000 écoles accédant au dashboard simultanément"""
        print("\n🚀 Test: 100 écoles → Dashboard simultané")
        
        results = []
        lock = Lock()
        
        def access_dashboard(school_index):
            try:
                client = Client()
                school = self.schools[school_index]
                client.login(username=school.user.username, password='testpass123')
                
                start = time.time()
                response = client.get(reverse('school_dashboard'))
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code == 200,
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code == 200, elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(access_dashboard, i) 
                      for i in range(100)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/100 ({successful}%)")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 95)
        self.assertLess(total_time, 30.0)
    
    def test_1000_mixed_operations_simultaneous(self):
        """1000 opérations mixtes simultanées (scénario réaliste)"""
        print("\n🚀 Test: 1000 opérations mixtes simultanées")
        
        results = []
        lock = Lock()
        operations = []
        
        def mixed_operation(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                operation_type = student_index % 5
                
                if operation_type == 0:
                    # Dashboard
                    response = client.get(reverse('dashboard'))
                elif operation_type == 1:
                    # Liste étudiants
                    response = client.get(reverse('student_list'))
                elif operation_type == 2:
                    # Like un post
                    post = self.posts[student_index % len(self.posts)]
                    response = client.post(reverse('like_post', args=[post.id]))
                elif operation_type == 3:
                    # Recherche
                    response = client.get(reverse('student_list'), {
                        'search': f'Stress{student_index % 100}'
                    })
                else:
                    # Conversations
                    response = client.get(reverse('conversations_list'))
                
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code in [200, 302],
                        'time': elapsed,
                        'type': operation_type
                    })
                    operations.append(operation_type)
                return response.status_code in [200, 302], elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(mixed_operation, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        # Compter les opérations par type
        op_counts = {}
        for op in operations:
            op_counts[op] = op_counts.get(op, 0) + 1
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        print(f"  📋 Répartition: Dashboard={op_counts.get(0,0)}, "
              f"Liste={op_counts.get(1,0)}, Likes={op_counts.get(2,0)}, "
              f"Recherche={op_counts.get(3,0)}, Messages={op_counts.get(4,0)}")
        
        self.assertGreater(successful, 950)
        self.assertLess(total_time, 120.0)
    
    def test_1000_groups_operations_simultaneous(self):
        """1000 opérations sur les groupes simultanément"""
        print("\n🚀 Test: 1000 étudiants → Opérations groupes simultanées")
        
        results = []
        lock = Lock()
        
        def group_operation(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                # Accéder à la liste des groupes
                response = client.get(reverse('groups_list'))
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code == 200,
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code == 200, elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(group_operation, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 950)
        self.assertLess(total_time, 60.0)
    
    def test_1000_events_operations_simultaneous(self):
        """1000 opérations sur les événements simultanément"""
        print("\n🚀 Test: 1000 étudiants → Opérations événements simultanées")
        
        results = []
        lock = Lock()
        
        def event_operation(student_index):
            try:
                client = Client()
                student = self.students[student_index]
                client.login(username=student.user.username, password='testpass123')
                
                start = time.time()
                # Accéder à la liste des événements
                response = client.get(reverse('events_list'))
                elapsed = time.time() - start
                
                with lock:
                    results.append({
                        'success': response.status_code == 200,
                        'time': elapsed,
                        'status': response.status_code
                    })
                return response.status_code == 200, elapsed
            except Exception as e:
                with lock:
                    results.append({
                        'success': False,
                        'time': 0,
                        'error': str(e)
                    })
                return False, 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(event_operation, i) 
                      for i in range(1000)]
            [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get('success', False))
        times = [r['time'] for r in results if r.get('success', False) and r['time'] > 0]
        
        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)
        else:
            avg_time = max_time = 0
        
        print(f"  ✅ Succès: {successful}/1000 ({successful/10:.1f}%)")
        print(f"  ⏱️  Temps total: {total_time:.2f}s")
        print(f"  📊 Temps moyen: {avg_time:.3f}s")
        print(f"  📊 Temps max: {max_time:.3f}s")
        
        self.assertGreater(successful, 950)
        self.assertLess(total_time, 60.0)

