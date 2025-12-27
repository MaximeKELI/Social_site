#!/usr/bin/env python
"""
Script pour exécuter tous les tests avec des rapports détaillés
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
    print("🧪 EXÉCUTION DES TESTS - SCHOOL SOCIAL")
    print("=" * 80)
    print()
    
    # Exécuter les tests
    failures = test_runner.run_tests([
        'social.tests.ModelTests',
        'social.tests.ViewTests',
        'social.tests.PerformanceTests',
        'social.tests.RealWorldScenarioTests',
        'social.tests.DatabaseQueryTests',
    ])
    
    print()
    print("=" * 80)
    print("📊 TESTS DE CHARGE")
    print("=" * 80)
    print()
    
    # Exécuter les tests de charge
    load_failures = test_runner.run_tests(['social.load_tests'])
    
    print()
    print("=" * 80)
    if failures or load_failures:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)
    else:
        print("✅ TOUS LES TESTS ONT RÉUSSI")
    print("=" * 80)

