#!/bin/bash

# Script de démarrage pour School Social

echo "🚀 Démarrage de School Social..."

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier si les migrations sont à jour
echo "📦 Vérification des migrations..."
python manage.py makemigrations --check --dry-run

# Appliquer les migrations si nécessaire
echo "🔄 Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques (pour la production)
# python manage.py collectstatic --noinput

# Démarrer le serveur
echo "✅ Démarrage du serveur Django..."
echo "🌐 Accédez à l'application sur http://127.0.0.1:8000/"
echo "🔧 Admin Django sur http://127.0.0.1:8000/admin/"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

python manage.py runserver

