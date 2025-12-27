"""
Vues pour le chatbot IA
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

# Import de l'API Google Gemini (déprécié mais fonctionnel)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai n'est pas installé")


@login_required
def chatbot_view(request):
    """Vue principale du chatbot"""
    return render(request, 'social/chatbot.html')


@login_required
@require_POST
def chatbot_api(request):
    """API endpoint pour interagir avec le chatbot"""
    if not GEMINI_AVAILABLE:
        return JsonResponse({
            'success': False,
            'error': 'Le service de chatbot n\'est pas disponible.'
        }, status=503)
    
    try:
        # Configuration de l'API (faite ici pour éviter les erreurs d'import)
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        
        # Récupérer le message de l'utilisateur
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Le message ne peut pas être vide'
            }, status=400)
        
        # Limiter la longueur du message
        if len(user_message) > 2000:
            return JsonResponse({
                'success': False,
                'error': 'Le message est trop long (max 2000 caractères)'
            }, status=400)
        
        # Obtenir le contexte de l'utilisateur
        user_context = ""
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            user_context = f"L'utilisateur est un étudiant nommé {student.full_name} de l'école {student.school.name}."
        elif hasattr(request.user, 'school_profile'):
            school = request.user.school_profile
            user_context = f"L'utilisateur est une école nommée {school.name}."
        
        # Créer le modèle Gemini
        model = genai.GenerativeModel('gemini-pro')
        
        # Construire le prompt avec contexte
        system_prompt = """Tu es un assistant IA intelligent et bienveillant pour une plateforme sociale scolaire.
Tu aides les étudiants et les écoles à naviguer sur la plateforme, répondre à leurs questions,
et fournir des conseils utiles. Sois amical, professionnel et concis dans tes réponses.
Réponds toujours en français."""
        
        full_prompt = f"{system_prompt}\n\n{user_context}\n\nUtilisateur: {user_message}\n\nAssistant:"
        
        # Générer la réponse
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1024,
            )
        )
        
        # Extraire le texte de la réponse
        bot_response = response.text.strip()
        
        # Log de sécurité
        from .security import log_security_event
        log_security_event('chatbot_interaction', request, {
            'message_length': len(user_message),
            'response_length': len(bot_response)
        })
        
        return JsonResponse({
            'success': True,
            'response': bot_response
        })
        
    except Exception as e:
        logger.error(f"Erreur dans chatbot_api: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Une erreur est survenue. Veuillez réessayer plus tard.'
        }, status=500)

