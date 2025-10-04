#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test rápido para verificar activación de agentes
"""

from src.services.rag_service import RAGService

print("=" * 70)
print("TEST: ACTIVACION DE AGENTES")
print("=" * 70)

# Inicializar
print("\nInicializando...")
rag = RAGService()
rag.initialize()

# Queries de prueba
test_queries = [
    ("Find research papers about deep learning", True),
    ("Search for academic studies on transformers", True),
    ("Find documents and synthesize the results", True),
    ("Search papers and combine research findings", True),
    ("What papers talk about NLP?", False),
    ("Hola, como estas?", False),
]

print("\n" + "=" * 70)
print("PROBANDO QUERIES")
print("=" * 70)

for query, should_activate in test_queries:
    print(f"\nQuery: '{query}'")
    print(f"Esperado: {'Agente' if should_activate else 'RAG Clasico'}")
    
    try:
        result = rag.query(query, include_sources=False)
        agent_used = result.get('agent_info', {}).get('agent_used')
        
        if agent_used:
            print(f"Resultado: AGENTE ({agent_used}) ✅")
            status = "✅ CORRECTO" if should_activate else "❌ INESPERADO"
        else:
            print(f"Resultado: RAG CLASICO")
            status = "✅ CORRECTO" if not should_activate else "❌ FALLO"
        
        print(f"Status: {status}")
        
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("-" * 70)

print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)
print("\nSi ves 'AGENTE' en las primeras 4 queries:")
print("  ✅ El sistema de agentes esta funcionando correctamente")
print("\nSi todas dicen 'RAG CLASICO':")
print("  ⚠️  El threshold es muy alto o las keywords no coinciden")
print("  💡 Solución: Bajar threshold de 0.4 a 0.3 en rag_service.py")
print("=" * 70)
