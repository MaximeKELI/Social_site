#!/bin/bash

# Script pour exécuter tous les tests de stress avec résumé

echo "🔥 TESTS DE STRESS EXTRÊMES - SCHOOL SOCIAL"
echo "============================================"
echo ""
echo "⚠️  ATTENTION: Ces tests simulent 1000 utilisateurs simultanés"
echo "   Ils peuvent prendre 10-30 minutes selon votre machine"
echo ""
read -p "Continuer? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

echo ""
echo "🚀 Démarrage des tests de stress..."
echo ""

# Activer l'environnement virtuel
source venv/bin/activate

# Exécuter les tests
python manage.py test social.stress_tests --verbosity=2

echo ""
echo "✅ Tests terminés !"
echo ""
echo "📊 Consultez STRESS_TESTING.md pour l'analyse des résultats"

