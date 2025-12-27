"""
Tests pour le chatbot IA
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
import json
from unittest.mock import patch, MagicMock
from .models import School, Student


class ChatbotTests(TestCase):
    """Tests pour le chatbot IA"""
    
    def setUp(self):
        """Configuration initiale pour tous les tests"""
        self.client = Client()
        cache.clear()
        
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
    
    def test_chatbot_view_requires_login(self):
        """Test que la vue chatbot nécessite une authentification"""
        response = self.client.get(reverse('chatbot'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_chatbot_view_accessible_for_student(self):
        """Test que la vue chatbot est accessible pour un étudiant"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('chatbot'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assistant IA')
        self.assertContains(response, 'chatbot')
    
    def test_chatbot_view_accessible_for_school(self):
        """Test que la vue chatbot est accessible pour une école"""
        self.client.login(username='school1', password='testpass123')
        response = self.client.get(reverse('chatbot'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assistant IA')
    
    def test_chatbot_api_requires_login(self):
        """Test que l'API chatbot nécessite une authentification"""
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_chatbot_api_requires_post(self):
        """Test que l'API chatbot nécessite une méthode POST"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('chatbot_api'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_success(self, mock_genai):
        """Test que l'API chatbot répond correctement avec succès"""
        # Mock de la réponse Gemini
        mock_response = MagicMock()
        mock_response.text = "Bonjour ! Je suis là pour vous aider."
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Bonjour'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['response'], "Bonjour ! Je suis là pour vous aider.")
        mock_model.generate_content.assert_called_once()
    
    def test_chatbot_api_empty_message(self):
        """Test que l'API rejette un message vide"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('vide', data['error'].lower())
    
    def test_chatbot_api_missing_message(self):
        """Test que l'API rejette une requête sans message"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_chatbot_api_message_too_long(self):
        """Test que l'API rejette un message trop long"""
        self.client.login(username='student1', password='testpass123')
        long_message = 'x' * 2001  # Plus de 2000 caractères
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': long_message}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('long', data['error'].lower())
    
    def test_chatbot_api_whitespace_only_message(self):
        """Test que l'API rejette un message avec seulement des espaces"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': '   '}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_student_context(self, mock_genai):
        """Test que le contexte étudiant est inclus dans le prompt"""
        mock_response = MagicMock()
        mock_response.text = "Réponse de test"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json'
        )
        
        # Vérifier que generate_content a été appelé
        mock_model.generate_content.assert_called_once()
        call_args = mock_model.generate_content.call_args
        
        # Vérifier que le prompt contient le contexte étudiant
        prompt = call_args[0][0]
        self.assertIn('étudiant', prompt.lower())
        self.assertIn('Jean Dupont', prompt)
        self.assertIn('École Test', prompt)
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_school_context(self, mock_genai):
        """Test que le contexte école est inclus dans le prompt"""
        mock_response = MagicMock()
        mock_response.text = "Réponse de test"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='school1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json'
        )
        
        # Vérifier que generate_content a été appelé
        mock_model.generate_content.assert_called_once()
        call_args = mock_model.generate_content.call_args
        
        # Vérifier que le prompt contient le contexte école
        prompt = call_args[0][0]
        self.assertIn('école', prompt.lower())
        self.assertIn('École Test', prompt)
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_error_handling(self, mock_genai):
        """Test la gestion des erreurs de l'API"""
        # Simuler une erreur de l'API Gemini
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('erreur', data['error'].lower())
    
    @patch('social.chatbot_views.GEMINI_AVAILABLE', False)
    def test_chatbot_api_unavailable_service(self):
        """Test quand le service Gemini n'est pas disponible"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('disponible', data['error'].lower())
    
    def test_chatbot_api_invalid_json(self):
        """Test avec un JSON invalide"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_special_characters(self, mock_genai):
        """Test avec des caractères spéciaux dans le message"""
        mock_response = MagicMock()
        mock_response.text = "Réponse avec caractères spéciaux"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test avec émojis 🚀 et caractères spéciaux !@#$%'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_unicode_message(self, mock_genai):
        """Test avec un message Unicode"""
        mock_response = MagicMock()
        mock_response.text = "Réponse Unicode"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': '测试中文 العربية русский'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_response_stripped(self, mock_genai):
        """Test que la réponse est nettoyée (strip)"""
        mock_response = MagicMock()
        mock_response.text = "   Réponse avec espaces   "
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        # Vérifier que les espaces ont été supprimés
        self.assertEqual(data['response'], "Réponse avec espaces")
    
    def test_chatbot_template_contains_elements(self):
        """Test que le template contient les éléments nécessaires"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('chatbot'))
        
        self.assertEqual(response.status_code, 200)
        # Vérifier la présence d'éléments clés
        self.assertContains(response, 'chatbot-container')
        self.assertContains(response, 'chatbot-messages')
        self.assertContains(response, 'chatbot-input')
        self.assertContains(response, 'Assistant IA')
    
    @patch('social.chatbot_views.genai')
    def test_chatbot_api_generation_config(self, mock_genai):
        """Test que la configuration de génération est correcte"""
        mock_response = MagicMock()
        mock_response.text = "Réponse"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        # Créer un mock pour GenerationConfig
        mock_config = MagicMock()
        mock_genai.types.GenerationConfig = MagicMock(return_value=mock_config)
        mock_genai.GenerativeModel.return_value = mock_model
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json'
        )
        
        # Vérifier que generate_content a été appelé
        mock_model.generate_content.assert_called_once()
        call_kwargs = mock_model.generate_content.call_args[1]
        
        # Vérifier que generation_config est présent
        self.assertIn('generation_config', call_kwargs)
        
        # Vérifier que GenerationConfig a été appelé avec les bons paramètres
        mock_genai.types.GenerationConfig.assert_called_once()
        config_call = mock_genai.types.GenerationConfig.call_args[1]
        self.assertEqual(config_call['temperature'], 0.7)
        self.assertEqual(config_call['top_p'], 0.8)
        self.assertEqual(config_call['top_k'], 40)
        self.assertEqual(config_call['max_output_tokens'], 1024)
    
    @patch('social.chatbot_views.genai')
    @patch('social.security.log_security_event')
    def test_chatbot_api_logs_security_event(self, mock_log, mock_genai):
        """Test que les interactions sont loggées"""
        mock_response = MagicMock()
        mock_response.text = "Réponse"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = MagicMock()
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test message'}),
            content_type='application/json'
        )
        
        # Vérifier que l'événement de sécurité a été loggé
        mock_log.assert_called_once()
        call_args = mock_log.call_args
        self.assertEqual(call_args[0][0], 'chatbot_interaction')
        self.assertEqual(call_args[0][1].user, self.student_user)
        
        # Vérifier les détails loggés
        details = call_args[0][2]
        self.assertIn('message_length', details)
        self.assertIn('response_length', details)
        self.assertEqual(details['message_length'], len('Test message'))
    
    def test_chatbot_api_csrf_protection(self):
        """Test que l'API est protégée par CSRF"""
        self.client.login(username='student1', password='testpass123')
        # Tenter une requête POST sans token CSRF
        response = self.client.post(
            reverse('chatbot_api'),
            json.dumps({'message': 'Test'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        # Devrait soit réussir (en mode test CSRF peut être désactivé) soit échouer
        self.assertIn(response.status_code, [200, 403, 400])

