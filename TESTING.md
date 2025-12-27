# Guide de Tests - School Social

Ce document décrit la suite de tests complète pour l'application School Social.

## 📋 Types de Tests

### 1. Tests Unitaires des Modèles (`ModelTests`)
Testent la création et le comportement de tous les modèles :
- ✅ Création d'écoles
- ✅ Création d'étudiants
- ✅ Création de posts, commentaires
- ✅ Système de likes
- ✅ Conversations et messages
- ✅ Notifications
- ✅ Groupes et événements

### 2. Tests des Vues (`ViewTests`)
Testent toutes les vues de l'application :
- ✅ Pages publiques (accueil, connexion)
- ✅ Authentification
- ✅ Dashboard
- ✅ Création de posts
- ✅ Système de likes
- ✅ Liste des étudiants
- ✅ Déconnexion

### 3. Tests de Performance (`PerformanceTests`)
Testent les performances avec des volumes de données réalistes :
- ✅ Dashboard avec 50 posts
- ✅ Liste de 100 étudiants
- ✅ Page de détail de post
- ✅ 50 likes simultanés
- ✅ Recherche
- ✅ Création massive de notifications (100)
- ✅ Création de messages (100)
- ✅ Opérations en masse (bulk operations)

### 4. Tests de Scénarios Réels (`RealWorldScenarioTests`)
Simulent des parcours utilisateurs complets :
- ✅ Parcours complet (inscription → connexion → utilisation)
- ✅ Interactions sociales (posts, likes, commentaires)
- ✅ Activités de groupe

### 5. Tests d'Optimisation (`DatabaseQueryTests`)
Vérifient l'optimisation des requêtes :
- ✅ Optimisation du dashboard (< 10 requêtes)
- ✅ Optimisation de la page post (< 5 requêtes)

### 6. Tests de Charge (`LoadTests`)
Simulent une utilisation intensive :
- ✅ 50 utilisateurs simultanés sur le dashboard
- ✅ 100 likes simultanés
- ✅ 30 posts créés simultanément
- ✅ 50 messages simultanés
- ✅ Test de stress avec 600 posts
- ✅ Test d'efficacité mémoire
- ✅ Gestion des connexions de base de données

## 🚀 Exécution des Tests

### Tous les tests
```bash
python manage.py test
```

### Tests spécifiques
```bash
# Tests unitaires
python manage.py test social.tests.ModelTests

# Tests de performance
python manage.py test social.tests.PerformanceTests

# Tests de charge
python manage.py test social.load_tests

# Tests avec verbosité
python manage.py test --verbosity=2
```

### Utiliser le script personnalisé
```bash
python run_tests.py
```

### Tests avec couverture de code
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Génère un rapport HTML
```

## 📊 Métriques de Performance

Les tests vérifient que :

| Opération | Temps Maximum | Données |
|-----------|---------------|---------|
| Dashboard | < 1.0s | 50 posts |
| Liste étudiants | < 0.5s | 100 étudiants |
| Page post | < 0.3s | 1 post + commentaires |
| 50 likes | < 2.0s | 50 opérations |
| Recherche | < 0.5s | 100 étudiants |
| 100 notifications | < 1.0s | 100 créations |
| 100 messages | < 1.0s | 100 créations |

### Tests de Charge

| Scénario | Utilisateurs | Temps Maximum |
|----------|--------------|---------------|
| Dashboard simultané | 50 | < 10.0s |
| Likes simultanés | 100 | < 5.0s |
| Posts simultanés | 30 | < 5.0s |
| Messages simultanés | 50 | < 10.0s |
| Dashboard stress | 1 | < 2.0s (600 posts) |

## 🔍 Analyse des Résultats

### Interprétation des résultats

1. **Tests réussis** : ✅ Tous les tests passent
2. **Tests échoués** : ❌ Vérifier les messages d'erreur
3. **Temps d'exécution** : Comparer avec les métriques attendues

### Optimisations possibles

Si les tests de performance échouent :
1. Vérifier les index de base de données
2. Optimiser les requêtes (select_related, prefetch_related)
3. Utiliser le cache si nécessaire
4. Vérifier la configuration de la base de données

## 📝 Ajout de Nouveaux Tests

Pour ajouter un nouveau test :

```python
def test_nouvelle_fonctionnalite(self):
    """Description du test"""
    # Arrange
    # Act
    # Assert
    self.assertEqual(...)
```

## 🛠️ Outils Recommandés

- **Django TestCase** : Tests de base
- **TransactionTestCase** : Tests avec transactions
- **Client** : Tests des vues HTTP
- **ThreadPoolExecutor** : Tests de concurrence
- **Coverage** : Couverture de code
- **django-debug-toolbar** : Profiling en développement

## 📈 Améliorations Futures

- [ ] Tests d'intégration avec Selenium
- [ ] Tests d'API REST
- [ ] Tests de sécurité
- [ ] Tests de compatibilité navigateurs
- [ ] Tests de montée en charge avec Locust
- [ ] Tests de régression automatiques

## ⚠️ Notes Importantes

1. Les tests de charge utilisent `TransactionTestCase` pour éviter les conflits
2. Les tests concurrents utilisent `ThreadPoolExecutor`
3. Les temps peuvent varier selon la machine
4. Utiliser `--keepdb` pour accélérer les tests répétés

---

**Dernière mise à jour** : Décembre 2025

