# Tests de Stress Extrêmes - School Social

## 🎯 Objectif

Ces tests simulent des conditions de production réelles avec **1000 utilisateurs simultanés** pour chaque type d'opération. Ils permettent de vérifier si l'application peut tenir en production.

## 📊 Tests Implémentés

### Tests Étudiants (1000 simultanés)

1. **Dashboard simultané**
   - 1000 étudiants accédant au dashboard en même temps
   - Vérifie: < 60s total, > 95% succès

2. **Création de posts simultanée**
   - 1000 étudiants créant des posts simultanément
   - Vérifie: < 120s total, > 95% succès, tous les posts créés

3. **Likes simultanés**
   - 1000 étudiants likant le même post
   - Vérifie: < 60s total, > 95% succès, tous les likes enregistrés

4. **Commentaires simultanés**
   - 1000 étudiants commentant le même post
   - Vérifie: < 120s total, > 95% succès

5. **Messages simultanés**
   - 1000 étudiants envoyant des messages
   - Vérifie: < 120s total, > 95% succès

6. **Recherche simultanée**
   - 1000 étudiants recherchant en même temps
   - Vérifie: < 60s total, > 95% succès

7. **Opérations groupes simultanées**
   - 1000 étudiants accédant aux groupes
   - Vérifie: < 60s total, > 95% succès

8. **Opérations événements simultanées**
   - 1000 étudiants accédant aux événements
   - Vérifie: < 60s total, > 95% succès

### Tests Écoles (100 simultanés)

9. **Dashboard écoles simultané**
   - 100 écoles accédant au dashboard
   - Vérifie: < 30s total, > 95% succès

### Tests Mixtes

10. **Opérations mixtes simultanées**
    - 1000 opérations variées (dashboard, recherche, likes, etc.)
    - Scénario réaliste de production
    - Vérifie: < 120s total, > 95% succès

## 🚀 Exécution

### Tous les tests de stress
```bash
python manage.py test social.stress_tests
```

### Test spécifique
```bash
python manage.py test social.stress_tests.ExtremeLoadTests.test_1000_students_dashboard_simultaneous
```

### Utiliser le script
```bash
python run_stress_tests.py
```

### Avec verbosité maximale
```bash
python manage.py test social.stress_tests --verbosity=2
```

## ⚠️ Avertissements

1. **Temps d'exécution**: Ces tests peuvent prendre 10-30 minutes selon votre machine
2. **Ressources**: Nécessite beaucoup de RAM et CPU
3. **Base de données**: Utilise TransactionTestCase (plus lent mais nécessaire)
4. **Concurrence**: Utilise ThreadPoolExecutor avec 200 workers max

## 📈 Métriques Attendues

| Test | Utilisateurs | Temps Max | Succès Min |
|------|--------------|-----------|------------|
| Dashboard étudiants | 1000 | 60s | 95% |
| Création posts | 1000 | 120s | 95% |
| Likes | 1000 | 60s | 95% |
| Commentaires | 1000 | 120s | 95% |
| Messages | 1000 | 120s | 95% |
| Recherche | 1000 | 60s | 95% |
| Dashboard écoles | 100 | 30s | 95% |
| Opérations mixtes | 1000 | 120s | 95% |

## 🔍 Analyse des Résultats

### Interprétation

- **✅ Succès > 95%**: Application prête pour la production
- **⚠️ Succès 90-95%**: Optimisations nécessaires
- **❌ Succès < 90%**: Problèmes critiques à résoudre

### Goulots d'étranglement possibles

1. **Base de données**
   - Ajouter des index
   - Optimiser les requêtes
   - Utiliser connection pooling

2. **Concurrence**
   - Vérifier les locks de base de données
   - Optimiser les transactions
   - Utiliser le cache

3. **Mémoire**
   - Vérifier les fuites mémoire
   - Optimiser les requêtes bulk
   - Limiter les résultats

## 🛠️ Optimisations Recommandées

### Base de données
```python
# Ajouter des index
class Meta:
    indexes = [
        models.Index(fields=['school', 'created_at']),
        models.Index(fields=['author', 'created_at']),
    ]
```

### Requêtes
```python
# Utiliser select_related et prefetch_related
posts = Post.objects.select_related('author', 'school').prefetch_related('likes', 'comments')
```

### Cache
```python
# Utiliser le cache pour les données fréquentes
from django.core.cache import cache
```

### Connexions
```python
# Configurer le pool de connexions
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,
    }
}
```

## 📝 Notes Techniques

- Utilise `ThreadPoolExecutor` avec 200 workers maximum
- Utilise `TransactionTestCase` pour éviter les conflits
- Mesure les temps individuels et agrégés
- Calcule les statistiques (moyenne, médiane, min, max)
- Gère les erreurs individuellement

## 🎯 Scénarios de Production

Ces tests simulent:
- Pic de trafic (1000 utilisateurs simultanés)
- Opérations intensives (création massive)
- Concurrence élevée (même ressource)
- Mix d'opérations (scénario réaliste)

## 📊 Exemple de Sortie

```
🚀 Test: 1000 étudiants → Dashboard simultané
  ✅ Succès: 987/1000 (98.7%)
  ⏱️  Temps total: 45.23s
  📊 Temps moyen: 0.234s
  📊 Temps médian: 0.198s
  📊 Temps min: 0.123s
  📊 Temps max: 2.456s
```

## 🔧 Configuration Recommandée

Pour des tests optimaux:
- CPU: 4+ cores
- RAM: 8GB+
- Base de données: SQLite en mémoire ou PostgreSQL
- Python: 3.8+

---

**Dernière mise à jour**: Décembre 2025

