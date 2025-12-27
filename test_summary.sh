#!/bin/bash

# Script de résumé des tests

echo "🧪 TESTS - SCHOOL SOCIAL"
echo "========================"
echo ""

echo "📊 Tests Unitaires des Modèles"
python manage.py test social.tests.ModelTests --verbosity=1
echo ""

echo "📊 Tests des Vues"
python manage.py test social.tests.ViewTests --verbosity=1
echo ""

echo "📊 Tests de Performance"
python manage.py test social.tests.PerformanceTests --verbosity=1
echo ""

echo "📊 Tests de Scénarios Réels"
python manage.py test social.tests.RealWorldScenarioTests --verbosity=1
echo ""

echo "📊 Tests d'Optimisation"
python manage.py test social.tests.DatabaseQueryTests --verbosity=1
echo ""

echo "✅ Tous les tests sont terminés !"
echo ""
echo "💡 Pour exécuter les tests de charge (plus longs) :"
echo "   python manage.py test social.load_tests"

