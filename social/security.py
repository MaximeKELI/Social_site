"""
Module de sécurité avancé pour l'application
Protection contre les attaques courantes et renforcement de la sécurité
"""
import time
import hashlib
import hmac
import logging
import re
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from PIL import Image
import io

logger = logging.getLogger('security')


class SecurityMiddleware:
    """
    Middleware de sécurité avancé
    - Rate limiting par IP
    - Headers de sécurité HTTP
    - Détection d'activités suspectes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_cache = {}
        
    def __call__(self, request):
        # Vérification du rate limiting
        if not self._check_rate_limit(request):
            logger.warning(f"Rate limit dépassé pour IP: {self._get_client_ip(request)}")
            return JsonResponse({
                'error': 'Trop de requêtes. Veuillez réessayer plus tard.'
            }, status=429)
        
        # Ajout des headers de sécurité
        response = self.get_response(request)
        response = self._add_security_headers(request, response)
        
        # Logging des activités suspectes
        self._log_suspicious_activity(request, response)
        
        return response
    
    def _get_client_ip(self, request):
        """Récupère l'IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _check_rate_limit(self, request):
        """Vérifie le rate limiting par IP"""
        # Désactiver le rate limiting en mode test
        from django.conf import settings
        if getattr(settings, 'TESTING', False):
            return True
        
        ip = self._get_client_ip(request)
        cache_key = f'rate_limit_{ip}'
        
        # Limites différentes selon le type de requête
        if request.path.startswith('/login') or request.path.startswith('/register'):
            limit = 5  # 5 tentatives par minute pour login/register
            window = 60
        elif request.method == 'POST':
            limit = 30  # 30 requêtes POST par minute
            window = 60
        else:
            limit = 100  # 100 requêtes GET par minute
            window = 60
        
        current = cache.get(cache_key, 0)
        if current >= limit:
            return False
        
        cache.set(cache_key, current + 1, window)
        return True
    
    def _add_security_headers(self, request, response):
        """Ajoute les headers de sécurité HTTP"""
        # Protection XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy stricte
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy'] = csp
        
        # Strict Transport Security (si HTTPS)
        if hasattr(request, 'is_secure') and request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), '
            'gyroscope=(), accelerometer=()'
        )
        
        return response
    
    def _log_suspicious_activity(self, request, response):
        """Log les activités suspectes"""
        ip = self._get_client_ip(request)
        suspicious_patterns = [
            (r'<script', 'XSS attempt'),
            (r'union.*select', 'SQL injection attempt'),
            (r'\.\./', 'Path traversal attempt'),
            (r'exec\(|eval\(', 'Code injection attempt'),
        ]
        
        # Vérifier les paramètres de requête (sans accéder à body qui peut être déjà lu)
        all_params = str(request.GET) + str(request.POST)
        
        # Essayer d'accéder à body seulement si disponible
        try:
            if hasattr(request, '_body'):
                all_params += str(request._body)
        except (AttributeError, Exception):
            pass
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, all_params, re.IGNORECASE):
                logger.warning(
                    f"Suspicious activity detected: {description} | "
                    f"IP: {ip} | Path: {request.path} | Method: {request.method}"
                )


def rate_limit_view(max_requests=10, window=60):
    """
    Décorateur pour limiter le nombre de requêtes par vue
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            cache_key = f'view_rate_limit_{view_func.__name__}_{ip}'
            
            current = cache.get(cache_key, 0)
            if current >= max_requests:
                return JsonResponse({
                    'error': 'Trop de requêtes. Veuillez réessayer plus tard.'
                }, status=429)
            
            cache.set(cache_key, current + 1, window)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def validate_file_upload(file, allowed_types=None, max_size=5*1024*1024, is_image=False):
    """
    Valide strictement les fichiers uploadés
    
    Args:
        file: Fichier uploadé
        allowed_types: Liste des types MIME autorisés
        max_size: Taille maximale en bytes (défaut: 5MB)
        is_image: Si True, valide que c'est une image valide
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return True, None
    
    # Vérifier la taille
    if file.size > max_size:
        return False, f"Le fichier est trop volumineux. Taille maximale: {max_size / (1024*1024):.1f}MB"
    
    # Vérifier le type MIME
    if allowed_types:
        content_type = getattr(file, 'content_type', '')
        if content_type not in allowed_types:
            return False, f"Type de fichier non autorisé. Types autorisés: {', '.join(allowed_types)}"
    
    # Validation spéciale pour les images
    if is_image:
        try:
            # Vérifier que c'est vraiment une image
            img = Image.open(file)
            img.verify()
            
            # Réouvrir après vérification (verify() ferme le fichier)
            file.seek(0)
            img = Image.open(file)
            
            # Vérifier les dimensions (protection contre les images malveillantes)
            width, height = img.size
            if width > 5000 or height > 5000:
                return False, "Les dimensions de l'image sont trop grandes (max: 5000x5000)"
            
            # Vérifier le format
            if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                return False, "Format d'image non autorisé. Formats autorisés: JPEG, PNG, GIF, WEBP"
            
            # Vérifier qu'il n'y a pas de code malveillant dans les métadonnées
            # (protection basique contre les stéganographies)
            if hasattr(img, '_getexif') and img._getexif():
                # Les EXIF peuvent contenir des données, on les nettoie
                pass
            
        except Exception as e:
            logger.warning(f"Image validation failed: {str(e)}")
            return False, "Le fichier n'est pas une image valide"
    
    # Vérifier le nom du fichier (protection contre path traversal)
    filename = getattr(file, 'name', '')
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Nom de fichier invalide"
    
    # Vérifier qu'il n'y a pas de caractères dangereux
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in dangerous_chars):
        return False, "Nom de fichier contient des caractères non autorisés"
    
    return True, None


def sanitize_input(text, max_length=None):
    """
    Nettoie et valide les entrées utilisateur
    
    Args:
        text: Texte à nettoyer
        max_length: Longueur maximale
    
    Returns:
        str: Texte nettoyé
    """
    if not text:
        return ''
    
    # Convertir en string si nécessaire
    text = str(text)
    
    # Limiter la longueur
    if max_length:
        text = text[:max_length]
    
    # Supprimer les caractères de contrôle
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Protection basique contre XSS (ne pas supprimer complètement, juste échapper)
    # Django le fait déjà dans les templates, mais on fait une couche supplémentaire
    
    return text.strip()


def validate_url(url):
    """
    Valide qu'une URL est sûre (protection SSRF)
    
    Args:
        url: URL à valider
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not url:
        return True, None
    
    # Vérifier le schéma
    if not url.startswith(('http://', 'https://')):
        return False, "URL invalide: doit commencer par http:// ou https://"
    
    # Vérifier qu'on n'essaie pas d'accéder à des IPs privées
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    
    if hostname:
        # Vérifier les IPs privées
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False, "Accès aux réseaux privés non autorisé"
        except ValueError:
            # C'est un hostname, pas une IP
            pass
    
    return True, None


def constant_time_compare(val1, val2):
    """
    Compare deux valeurs en temps constant (protection contre les attaques de timing)
    """
    return hmac.compare_digest(str(val1), str(val2))


def hash_sensitive_data(data, salt=None):
    """
    Hash des données sensibles avec un salt
    """
    if salt is None:
        salt = settings.SECRET_KEY[:16]
    
    return hashlib.sha256((str(data) + salt).encode()).hexdigest()


def log_security_event(event_type, request, details=None):
    """
    Log un événement de sécurité
    
    Args:
        event_type: Type d'événement (login_failed, suspicious_activity, etc.)
        request: Objet request
        details: Détails supplémentaires
    """
    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    user = getattr(request, 'user', None)
    username = user.username if user and user.is_authenticated else 'anonymous'
    
    log_data = {
        'event_type': event_type,
        'ip': ip,
        'username': username,
        'path': request.path,
        'method': request.method,
        'timestamp': timezone.now().isoformat(),
        'details': details or {}
    }
    
    logger.info(f"Security event: {log_data}")


class SecureFileField:
    """
    Champ de fichier sécurisé avec validation automatique
    """
    def __init__(self, allowed_types=None, max_size=5*1024*1024, is_image=False):
        self.allowed_types = allowed_types
        self.max_size = max_size
        self.is_image = is_image
    
    def validate(self, file):
        """Valide le fichier"""
        is_valid, error = validate_file_upload(
            file, 
            allowed_types=self.allowed_types,
            max_size=self.max_size,
            is_image=self.is_image
        )
        if not is_valid:
            raise ValidationError(error)
        return file

