#!/usr/bin/env python
"""
Script pour exécuter les tests de stress extrêmes
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'school_social.settings'
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    print("=" * 80)
    print("🔥 TESTS DE STRESS EXTRÊMES - 1000 UTILISATEURS SIMULTANÉS")
    print("=" * 80)
    print()
    print("⚠️  ATTENTION: Ces tests sont très intensifs et peuvent prendre du temps")
    print("   Ils simulent des conditions de production réelles")
    print()
    
    # Exécuter les tests de stress
    failures = test_runner.run_tests(['social.stress_tests'])
    
    print()
    print("=" * 80)
    if failures:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("   Analysez les résultats pour identifier les goulots d'étranglement")
        sys.exit(1)
    else:
        print("✅ TOUS LES TESTS DE STRESS ONT RÉUSSI")
        print("   L'application est prête pour la production !")
    print("=" * 80)

