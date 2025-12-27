# 🚀 Guide Rapide - Tests de Stress

## Exécution Rapide

```bash
# Tous les tests de stress (10 tests, ~10-30 min)
python manage.py test social.stress_tests

# Un test spécifique (plus rapide)
python manage.py test social.stress_tests.ExtremeLoadTests.test_1000_students_likes_simultaneous

# Avec le script
./run_all_stress_tests.sh
```

## Tests Disponibles

### Étudiants (1000 simultanés)
1. `test_1000_students_dashboard_simultaneous` - Dashboard
2. `test_1000_students_create_posts_simultaneous` - Création posts
3. `test_1000_students_likes_simultaneous` - Likes
4. `test_1000_students_comments_simultaneous` - Commentaires
5. `test_1000_students_messages_simultaneous` - Messages
6. `test_1000_students_search_simultaneous` - Recherche
7. `test_1000_groups_operations_simultaneous` - Groupes
8. `test_1000_events_operations_simultaneous` - Événements

### Écoles (100 simultanés)
9. `test_1000_schools_dashboard_simultaneous` - Dashboard écoles

### Mixte
10. `test_1000_mixed_operations_simultaneous` - Opérations variées

## Critères de Succès

- ✅ **> 95% de succès** = Prêt pour production
- ⚠️ **90-95%** = Optimisations nécessaires
- ❌ **< 90%** = Problèmes critiques

## Temps d'Exécution Estimés

| Test | Temps Estimé |
|------|--------------|
| Dashboard | 30-60s |
| Création posts | 60-120s |
| Likes | 30-60s |
| Commentaires | 60-120s |
| Messages | 60-120s |
| Recherche | 30-60s |
| **TOTAL** | **10-30 min** |

## Optimisations Si Échecs

1. **Base de données lente**: Ajouter des index
2. **Concurrence**: Vérifier les locks
3. **Mémoire**: Optimiser les requêtes
4. **Timeout**: Augmenter les timeouts

---

Pour plus de détails, voir `STRESS_TESTING.md`

