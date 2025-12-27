# Documentation de Sécurité - School Social

## Vue d'ensemble

Ce document décrit toutes les mesures de sécurité ultra-renforcées implémentées dans l'application School Social. Toutes ces mesures sont **transparentes pour l'utilisateur final** et fonctionnent en arrière-plan.

## 🔒 Mesures de Sécurité Implémentées

### 1. Middleware de Sécurité Avancé (`social/security.py`)

#### Rate Limiting par IP
- **Login/Register**: 5 tentatives par minute
- **Requêtes POST**: 30 par minute
- **Requêtes GET**: 100 par minute
- Blocage automatique avec message d'erreur approprié

#### Headers de Sécurité HTTP
- **X-Content-Type-Options**: `nosniff` - Empêche le MIME-sniffing
- **X-Frame-Options**: `DENY` - Protection contre le clickjacking
- **X-XSS-Protection**: `1; mode=block` - Protection XSS du navigateur
- **Content-Security-Policy**: Politique stricte limitant les ressources
- **Strict-Transport-Security**: Force HTTPS (si activé)
- **Referrer-Policy**: Contrôle des informations de référent
- **Permissions-Policy**: Désactive les APIs sensibles

#### Détection d'Activités Suspectes
- Détection automatique de patterns malveillants :
  - Tentatives XSS (`<script`)
  - Tentatives d'injection SQL (`union select`)
  - Tentatives de path traversal (`../`)
  - Tentatives d'injection de code (`exec(`, `eval(`)
- Logging automatique de toutes les activités suspectes

### 2. Validation Stricte des Fichiers Uploadés

#### Validations Implémentées
- **Taille maximale**: 5MB par défaut (configurable)
- **Types MIME autorisés**: JPEG, PNG, GIF, WEBP uniquement
- **Validation d'image réelle**: Vérification que le fichier est vraiment une image
- **Dimensions maximales**: 5000x5000 pixels
- **Protection path traversal**: Rejet des noms de fichiers avec `..`, `/`, `\`
- **Caractères dangereux**: Rejet des caractères spéciaux dans les noms de fichiers
- **Vérification des métadonnées**: Nettoyage des EXIF potentiellement malveillants

### 3. Sanitization des Entrées Utilisateur

#### Fonction `sanitize_input()`
- Suppression des caractères de contrôle
- Limitation de longueur (configurable par champ)
- Nettoyage des espaces en début/fin
- Protection basique contre XSS (couche supplémentaire)

#### Application dans les Formulaires
- Tous les champs texte sont nettoyés automatiquement
- Validation de longueur maximale
- Validation de format (email, téléphone, etc.)

### 4. Protection CSRF Renforcée

#### Configurations (`settings.py`)
- **CSRF_COOKIE_HTTPONLY**: `True` - Empêche l'accès JavaScript au cookie
- **CSRF_COOKIE_SAMESITE**: `Strict` - Protection contre les attaques cross-site
- **CSRF_USE_SESSIONS**: `True` - Stockage du token dans la session

### 5. Sécurisation des Sessions

#### Configurations
- **SESSION_COOKIE_HTTPONLY**: `True` - Empêche l'accès JavaScript
- **SESSION_COOKIE_SAMESITE**: `Strict` - Protection cross-site
- **SESSION_COOKIE_AGE**: 3600 secondes (1 heure)
- **SESSION_EXPIRE_AT_BROWSER_CLOSE**: `True`
- **SESSION_SAVE_EVERY_REQUEST**: `True` - Renouvellement à chaque requête

### 6. Protection contre les Attaques par Force Brute

#### Login Renforcé
- Rate limiting: 5 tentatives par minute par IP
- Logging de toutes les tentatives (succès et échecs)
- Délai d'attente après échecs multiples
- Protection contre les attaques de timing (comparaison en temps constant)

### 7. Validation des URLs (Protection SSRF)

#### Fonction `validate_url()`
- Vérification du schéma (http/https uniquement)
- Blocage des IPs privées (10.x.x.x, 192.168.x.x, 127.x.x.x, etc.)
- Blocage des IPs loopback et link-local
- Validation du format d'URL

### 8. Logging de Sécurité

#### Événements Loggés
- Tentatives de connexion (succès/échec)
- Activités suspectes détectées
- Tentatives d'accès non autorisées
- Création/modification de contenu
- Erreurs de validation

#### Format des Logs
- Fichier: `logs/security.log`
- Format: JSON-like avec timestamp, IP, username, action, détails
- Rotation automatique (gérée par Django)

### 9. Validation des Permissions

#### Vérifications Implémentées
- Vérification que l'utilisateur est actif avant toute action
- Vérification du type d'utilisateur (étudiant/école)
- Vérification de l'appartenance à la même école
- Vérification de la propriété des ressources (posts, messages, etc.)

### 10. Protection contre les Attaques de Timing

#### Fonction `constant_time_compare()`
- Comparaison en temps constant pour les valeurs sensibles
- Utilisation de `hmac.compare_digest()` pour éviter les fuites d'information

## 📋 Configuration de Sécurité

### Variables dans `settings.py`

```python
# Limites de sécurité
SECURITY_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
SECURITY_ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
SECURITY_RATE_LIMIT_LOGIN = 5  # Tentatives de connexion par minute
SECURITY_RATE_LIMIT_POST = 30  # Requêtes POST par minute
SECURITY_RATE_LIMIT_GET = 100  # Requêtes GET par minute
```

### Middleware Actif

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "social.security.SecurityMiddleware",  # ← Notre middleware personnalisé
    # ... autres middlewares
]
```

## 🔍 Points de Contrôle de Sécurité

### Formulaires Sécurisés
- ✅ `SchoolRegistrationForm` - Validation logo + sanitization
- ✅ `StudentRegistrationForm` - Validation photo + sanitization
- ✅ `PostForm` - Validation image + sanitization
- ✅ `CommentForm` - Sanitization contenu
- ✅ `MessageForm` - Sanitization contenu

### Vues Sécurisées
- ✅ `login_view` - Rate limiting + logging
- ✅ `create_post` - Validation fichier + logging
- ✅ `like_post` - Validation ID + vérification permissions
- ✅ `edit_profile` - Sanitization + validation fichier
- ✅ `student_list` - Sanitization recherche

## 🚨 Réponse aux Incidents

### En cas d'activité suspecte détectée
1. **Logging automatique** dans `logs/security.log`
2. **Blocage temporaire** de l'IP (rate limiting)
3. **Message générique** à l'utilisateur (pas de détails techniques)
4. **Alerte** dans les logs pour investigation

### Monitoring Recommandé
- Surveiller `logs/security.log` régulièrement
- Configurer des alertes pour patterns suspects
- Analyser les tentatives de connexion échouées
- Surveiller les uploads de fichiers

## 🔐 Bonnes Pratiques Implémentées

1. **Principe du moindre privilège**: Vérification systématique des permissions
2. **Défense en profondeur**: Plusieurs couches de sécurité
3. **Fail-secure**: En cas de doute, refuser l'accès
4. **Transparence**: Aucun impact sur l'expérience utilisateur
5. **Logging complet**: Traçabilité de toutes les actions sensibles

## 📝 Notes de Production

### À activer en production
```python
DEBUG = False
ALLOWED_HOSTS = ['votre-domaine.com']
CSRF_COOKIE_SECURE = True  # HTTPS requis
SESSION_COOKIE_SECURE = True  # HTTPS requis
SECURE_SSL_REDIRECT = True  # Redirection HTTPS forcée
SECURE_HSTS_SECONDS = 31536000  # HSTS activé
```

### Génération d'une SECRET_KEY sécurisée
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## ✅ Tests de Sécurité

Tous les tests unitaires passent avec les nouvelles mesures de sécurité :
- ✅ Tests de modèles
- ✅ Tests de vues
- ✅ Tests de performance
- ✅ Tests de scénarios réels

## 🔄 Maintenance

- **Mise à jour régulière** de Django et des dépendances
- **Révision périodique** des logs de sécurité
- **Tests de pénétration** recommandés
- **Mise à jour** des patterns de détection d'activités suspectes

---

**Dernière mise à jour**: $(date)
**Version**: 1.0
**Statut**: ✅ Production Ready

