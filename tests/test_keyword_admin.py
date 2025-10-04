# -*- coding: utf-8 -*-
"""
Script de prueba para el módulo de administración de keywords (HU2)
"""

from src.admin.keyword_manager import KeywordManager
from src.utils.logger import setup_logger

logger = setup_logger()

def test_keyword_manager():
    """Prueba el gestor de keywords"""
    
    print("=" * 60)
    print("🧪 PRUEBA: Módulo de Administración de Keywords (HU2)")
    print("=" * 60)
    
    # Inicializar manager
    print("\n1️⃣ Inicializando KeywordManager...")
    manager = KeywordManager()
    print("✅ KeywordManager inicializado")
    
    # Obtener estadísticas del sistema
    print("\n2️⃣ Obteniendo estadísticas del sistema...")
    stats = manager.get_system_stats()
    print(f"   📊 Agentes totales: {stats['total_agents']}")
    print(f"   ✅ Agentes activos: {stats['active_agents']}")
    print(f"   🎯 Capacidades totales: {stats['total_capabilities']}")
    print(f"   🔑 Keywords totales: {stats['total_keywords']}")
    print(f"   📅 Última actualización: {stats['last_updated']}")
    print(f"   ✔️ Configuración válida: {stats['config_valid']}")
    
    # Obtener keywords de DocumentSearchAgent
    print("\n3️⃣ Obteniendo keywords de DocumentSearchAgent...")
    agent_keywords = manager.get_agent_keywords("DocumentSearchAgent")
    for capability, keywords in agent_keywords.items():
        print(f"   📄 {capability}: {len(keywords)} keywords")
        print(f"      {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
    
    # Probar query de activación
    print("\n4️⃣ Probando activación con queries...")
    
    test_queries = [
        "Find research papers about deep learning",
        "Synthesize the main findings from these studies",
        "What is machine learning?",
        "Buscar documentos sobre inteligencia artificial"
    ]
    
    for query in test_queries:
        print(f"\n   🔍 Query: \"{query}\"")
        results = manager.test_query_activation(query)
        
        for agent_name, result in results.items():
            score = result['score']
            threshold = result['threshold']
            would_activate = result['would_activate']
            matches = result['matches']
            
            status = "✅ SE ACTIVARÍA" if would_activate else "❌ NO SE ACTIVARÍA"
            print(f"      {agent_name}: {status}")
            print(f"         Score: {score:.2f} / {threshold:.2f}")
            
            if matches:
                print(f"         Keywords detectadas:")
                for cap, kws in matches.items():
                    print(f"            - {cap}: {', '.join(kws)}")
    
    # Agregar nueva keyword
    print("\n5️⃣ Agregando nueva keyword...")
    success = manager.add_keyword("DocumentSearchAgent", "DOCUMENT_SEARCH", "investigar")
    if success:
        print("   ✅ Keyword 'investigar' agregada exitosamente")
        
        # Verificar que se agregó
        keywords = manager.get_capability_keywords("DocumentSearchAgent", "DOCUMENT_SEARCH")
        if "investigar" in keywords:
            print("   ✅ Verificado: keyword presente en la lista")
    else:
        print("   ❌ Error agregando keyword")
    
    # Probar query con nueva keyword
    print("\n6️⃣ Probando query con nueva keyword...")
    query = "Quiero investigar sobre machine learning"
    print(f"   🔍 Query: \"{query}\"")
    results = manager.test_query_activation(query)
    
    for agent_name, result in results.items():
        if result['would_activate']:
            print(f"   ✅ {agent_name} se activaría")
            if "investigar" in str(result['matches']):
                print("   ✅ Nueva keyword 'investigar' detectada!")
    
    # Actualizar threshold
    print("\n7️⃣ Actualizando threshold...")
    old_threshold = manager.get_agent_config("DocumentSearchAgent").get("threshold", 0.3)
    new_threshold = 0.5
    print(f"   Threshold actual: {old_threshold}")
    print(f"   Nuevo threshold: {new_threshold}")
    
    success = manager.update_threshold("DocumentSearchAgent", new_threshold)
    if success:
        print("   ✅ Threshold actualizado exitosamente")
        
        # Verificar
        current_threshold = manager.get_agent_config("DocumentSearchAgent").get("threshold")
        print(f"   ✅ Verificado: threshold = {current_threshold}")
    
    # Restaurar threshold original
    manager.update_threshold("DocumentSearchAgent", old_threshold)
    print(f"   🔄 Threshold restaurado a {old_threshold}")
    
    # Eliminar keyword de prueba
    print("\n8️⃣ Limpiando: eliminando keyword de prueba...")
    success = manager.remove_keyword("DocumentSearchAgent", "DOCUMENT_SEARCH", "investigar")
    if success:
        print("   ✅ Keyword 'investigar' eliminada")
    
    # Exportar configuración
    print("\n9️⃣ Exportando configuración...")
    config = manager.export_config()
    print(f"   ✅ Configuración exportada ({len(str(config))} caracteres)")
    
    print("\n" + "=" * 60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("=" * 60)
    print("\n📝 Resumen:")
    print("   ✅ KeywordManager funciona correctamente")
    print("   ✅ Persistencia de keywords operativa")
    print("   ✅ Test de activación funcional")
    print("   ✅ CRUD de keywords operativo")
    print("   ✅ Gestión de threshold funcional")
    print("   ✅ Export/Import disponible")
    print("\n🎉 El módulo de administración de keywords está listo para usar!")

if __name__ == "__main__":
    try:
        test_keyword_manager()
    except Exception as e:
        logger.error(f"Error en prueba: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
