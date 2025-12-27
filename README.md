# School Social - Plateforme Sociale pour Écoles

Une application web Django complète qui permet aux écoles de s'inscrire et aux étudiants (actuels et anciens) de se connecter, discuter et interagir entre eux.

## 🚀 Fonctionnalités

### Pour les Écoles
- ✅ Inscription et gestion de compte
- ✅ Tableau de bord avec statistiques
- ✅ Visualisation des étudiants inscrits
- ✅ Suivi des posts publiés

### Pour les Étudiants
- ✅ Inscription et authentification
- ✅ Profil personnalisable avec photo
- ✅ Publication de posts avec images
- ✅ Système de likes et commentaires
- ✅ Messagerie privée entre étudiants
- ✅ Liste des étudiants de l'école
- ✅ Recherche d'étudiants
- ✅ Groupes et clubs
- ✅ Événements scolaires
- ✅ Système de notifications
- ✅ Édition de profil

### Fonctionnalités Sociales
- 📝 **Posts** : Création, modification, suppression de posts avec images
- 💬 **Commentaires** : Commenter les posts des autres
- ❤️ **Likes** : Aimer les posts
- 💌 **Messagerie** : Conversations privées entre étudiants
- 👥 **Groupes** : Création et gestion de groupes/clubs
- 📅 **Événements** : Organisation et participation aux événements
- 🔔 **Notifications** : Notifications pour les interactions
- 🔍 **Recherche** : Recherche d'étudiants et de groupes

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

## 🛠️ Installation

1. **Cloner ou télécharger le projet**
   ```bash
   cd /home/maxime/social_Site
   ```

2. **Activer l'environnement virtuel**
   ```bash
   source venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Effectuer les migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Créer un superutilisateur (optionnel, pour l'admin Django)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

7. **Accéder à l'application**
   - Application : http://127.0.0.1:8000/
   - Admin Django : http://127.0.0.1:8000/admin/

## 📁 Structure du Projet

```
social_Site/
├── school_social/          # Configuration du projet Django
│   ├── settings.py         # Paramètres de l'application
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # Configuration WSGI
├── social/                 # Application principale
│   ├── models.py          # Modèles de données
│   ├── views.py           # Vues de l'application
│   ├── forms.py           # Formulaires
│   ├── urls.py            # URLs de l'application
│   ├── admin.py           # Configuration admin
│   └── migrations/        # Migrations de base de données
├── templates/              # Templates HTML
│   └── social/            # Templates de l'application
├── static/                 # Fichiers statiques (CSS, JS, images)
├── media/                  # Fichiers uploadés (photos, logos)
├── db.sqlite3             # Base de données SQLite
├── requirements.txt       # Dépendances Python
└── README.md              # Ce fichier
```

## 🗄️ Modèles de Données

- **School** : Informations sur les écoles
- **Student** : Profils des étudiants
- **Post** : Posts publiés sur le mur
- **Comment** : Commentaires sur les posts
- **Conversation** : Conversations entre étudiants
- **Message** : Messages dans les conversations
- **Notification** : Notifications pour les utilisateurs
- **Group** : Groupes/clubs d'étudiants
- **Event** : Événements organisés

## 🎨 Interface Utilisateur

L'application utilise Bootstrap 5 pour une interface moderne et responsive avec :
- Design moderne et élégant
- Navigation intuitive
- Cartes interactives
- Formulaires stylisés
- Messages de notification
- Interface responsive (mobile-friendly)

## 🔐 Sécurité

- Authentification Django intégrée
- Protection CSRF
- Validation des formulaires
- Restrictions d'accès par décorateurs
- Gestion sécurisée des fichiers uploadés

## 📝 Utilisation

### Inscription d'une École
1. Aller sur la page d'accueil
2. Cliquer sur "Inscription École"
3. Remplir le formulaire avec les informations de l'école
4. Se connecter avec les identifiants créés

### Inscription d'un Étudiant
1. Aller sur la page d'accueil
2. Cliquer sur "Inscription Étudiant"
3. Remplir le formulaire (choisir l'école)
4. Se connecter avec les identifiants créés

### Fonctionnalités Étudiant
- **Dashboard** : Voir le fil d'actualité de l'école
- **Créer un post** : Publier du contenu avec texte et images
- **Étudiants** : Voir la liste des étudiants et leurs profils
- **Messages** : Discuter en privé avec d'autres étudiants
- **Groupes** : Créer ou rejoindre des groupes
- **Événements** : Créer ou participer à des événements
- **Notifications** : Voir les notifications d'activité

## 🚧 Améliorations Futures Possibles

- [ ] Chat en temps réel avec WebSockets
- [ ] Système de tags/hashtags
- [ ] Partage de fichiers
- [ ] Système de modération
- [ ] Export de données
- [ ] API REST
- [ ] Application mobile
- [ ] Intégration avec réseaux sociaux externes

## 📄 Licence

Ce projet est un exemple éducatif. Libre d'utilisation et de modification.

## 👨‍💻 Développement

Pour contribuer ou modifier le projet :
1. Créer une branche pour vos modifications
2. Tester vos changements
3. Effectuer les migrations si nécessaire
4. Soumettre vos modifications

## 📞 Support

Pour toute question ou problème, consultez la documentation Django : https://docs.djangoproject.com/

---

**Développé avec Django 5.2.9**
