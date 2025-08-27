#!/usr/bin/env python3
"""
Test rapide pour vérifier que le RAG (système de base de connaissances) fonctionne
"""
import os
import sys
sys.path.append('/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA/E3_model_IA/scripts')

print("🔍 Test du système RAG...")

# Test d'accès aux fichiers de connaissances
knowledge_base_path = "/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA/E3_model_IA/knowledge_base"

print(f"📂 Vérification du chemin : {knowledge_base_path}")
if os.path.exists(knowledge_base_path):
    print("✅ Répertoire knowledge_base trouvé")
    
    # Compter les fichiers
    count = 0
    for root, dirs, files in os.walk(knowledge_base_path):
        for file in files:
            if file.endswith('.md'):
                count += 1
                print(f"   📄 {file}")
    
    print(f"✅ {count} fichiers .md trouvés dans la base de connaissances")
else:
    print("❌ Répertoire knowledge_base NON trouvé")

# Test d'import de l'agent
print("\n🤖 Test d'import de l'agent...")
try:
    from advanced_agent import get_training_knowledge, knowledge_retriever
    print("✅ Import de l'agent réussi")
    
    if knowledge_retriever is not None:
        print("✅ Knowledge retriever initialisé")
        
        # Test de recherche simple
        print("\n🔎 Test de recherche dans la base de connaissances...")
        try:
            result = get_training_knowledge("VMA")
            print(f"✅ Recherche 'VMA' réussie:")
            print(f"Résultat (premiers 200 chars): {result[:200]}...")
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
    else:
        print("❌ Knowledge retriever est None - problème d'initialisation")
        
except Exception as e:
    print(f"❌ Erreur d'import: {e}")

print("\n🏁 Test terminé")