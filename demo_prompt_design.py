#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo del Sistema de Prompt Design Dinámico
Muestra cómo usar el sistema de configuración de prompts por sector
"""

from src.admin.prompt_design_manager import PromptDesignManager
from src.utils.dynamic_prompt_orchestrator import DynamicPromptOrchestrator
from src.utils.intent_detector import intent_detector
import asyncio


def print_separator(title=""):
    """Imprime separador visual"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def demo_list_sectors():
    """Demuestra cómo listar sectores disponibles"""
    print_separator("DEMO 1: Listar Sectores Disponibles")

    manager = PromptDesignManager()
    orchestrator = DynamicPromptOrchestrator()

    # Obtener sectores
    sectors = orchestrator.get_available_sectors()

    print("📚 Sectores Configurados:\n")
    for sector_id, info in sectors.items():
        status = "✅ ACTIVO" if info['is_active'] else "📋"
        enabled = "✔️" if info['enabled'] else "❌"
        print(f"{status} {enabled} {info['name']}")
        print(f"   ID: {sector_id}")
        print(f"   Descripción: {info['description']}")
        print(f"   Intent Prompts: {info['intent_prompts_count']}")
        print(f"   Guidelines: {info['guidelines_count']}")
        print()


def demo_change_sector():
    """Demuestra cómo cambiar el sector activo"""
    print_separator("DEMO 2: Cambiar Sector Activo")

    manager = PromptDesignManager()

    # Ver sector actual
    current_id, current_config = manager.get_active_sector()
    print(f"📍 Sector actual: {current_config.get('name', current_id)}")

    # Cambiar a business_analysis
    print("\n🔄 Cambiando a 'business_analysis'...")
    success = manager.set_active_sector("business_analysis")

    if success:
        new_id, new_config = manager.get_active_sector()
        print(f"✅ Sector activo ahora: {new_config.get('name', new_id)}")
        print(f"   Descripción: {new_config.get('description', '')}")
    else:
        print("❌ Error al cambiar sector")

    # Volver al sector original
    print(f"\n🔄 Restaurando sector original: {current_config.get('name', current_id)}")
    manager.set_active_sector(current_id)


def demo_create_custom_sector():
    """Demuestra cómo crear un sector personalizado"""
    print_separator("DEMO 3: Crear Sector Personalizado")

    manager = PromptDesignManager()

    sector_id = "marketing_analysis"
    sector_name = "Análisis de Marketing"
    description = "Análisis de estrategias de marketing y comportamiento del consumidor"
    system_prompt = """Eres un analista de marketing experto que proporciona insights sobre estrategias de marketing, análisis de mercado y comportamiento del consumidor.

Tu enfoque es estratégico, basado en datos y orientado a resultados medibles."""

    guidelines = [
        "Enfócate en métricas de marketing (ROI, CAC, LTV, tasa de conversión)",
        "Proporciona ejemplos de campañas exitosas cuando sea relevante",
        "Analiza segmentación de mercado y buyer personas",
        "Considera tendencias digitales y comportamiento del consumidor",
        "Usa datos y estadísticas para respaldar recomendaciones"
    ]

    print(f"🎨 Creando sector personalizado: {sector_name}")
    print(f"   ID: {sector_id}")
    print(f"   Guidelines: {len(guidelines)}")

    try:
        success = manager.create_custom_sector(
            sector_id=sector_id,
            name=sector_name,
            description=description,
            system_prompt=system_prompt,
            guidelines=guidelines
        )

        if success:
            print(f"\n✅ Sector '{sector_name}' creado exitosamente!")

            # Verificar que se creó
            sector_info = manager.get_sector_info(sector_id)
            print(f"\n📋 Configuración del sector:")
            print(f"   Nombre: {sector_info['name']}")
            print(f"   Directrices: {len(sector_info['response_guidelines'])}")
            print(f"   Intent Prompts: {len(sector_info['intent_prompts'])}")

        else:
            print("❌ Error al crear sector (puede que ya exista)")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if "ya existe" in str(e).lower():
            print("   El sector ya fue creado en una ejecución anterior")


def demo_test_prompts():
    """Demuestra cómo probar prompts para diferentes sectores"""
    print_separator("DEMO 4: Probar Prompts por Sector")

    orchestrator = DynamicPromptOrchestrator()

    test_queries = [
        ("business_analysis", "¿Cuáles son las oportunidades de crecimiento en el mercado?"),
        ("legal_review", "Analiza las cláusulas de este contrato"),
        ("technical_documentation", "Explica la arquitectura del sistema"),
    ]

    for sector_id, query in test_queries:
        print(f"\n🎯 Sector: {sector_id}")
        print(f"   Query: {query}")

        try:
            # Activar sector
            manager = PromptDesignManager()
            manager.set_active_sector(sector_id)

            # Obtener prompts
            preview = orchestrator.get_prompt_preview(sector_id, "GENERAL")

            print(f"\n   📋 System Prompt (primeros 150 chars):")
            print(f"      {preview['system_prompt'][:150]}...")

            print(f"\n   ✨ Guidelines:")
            for guideline in preview['guidelines'][:3]:
                print(f"      • {guideline}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


async def demo_with_intent_detection():
    """Demuestra integración con detección de intención"""
    print_separator("DEMO 5: Integración con Detección de Intención")

    orchestrator = DynamicPromptOrchestrator()
    manager = PromptDesignManager()

    # Cambiar a sector académico
    manager.set_active_sector("academic_research")

    test_query = "Compare the methodologies of transformer architectures vs RNNs"

    print(f"📝 Query: {test_query}")

    # Detectar intención
    intent_result = await intent_detector.detect_intent(test_query)

    print(f"\n🎯 Intención detectada: {intent_result.intent_type.value}")
    print(f"   Confidence: {intent_result.confidence:.2f}")

    # Obtener prompts dinámicos
    dynamic_result = orchestrator.get_prompts_for_query(
        query=test_query,
        intent_result=intent_result
    )

    print(f"\n📊 Configuración seleccionada:")
    print(f"   Sector: {dynamic_result.sector_name}")
    print(f"   Intent Type: {dynamic_result.intent_type}")
    print(f"   Guidelines: {len(dynamic_result.guidelines)}")

    print(f"\n🤖 System Prompt (primeros 200 chars):")
    print(f"   {dynamic_result.system_prompt[:200]}...")

    print(f"\n📋 Guidelines aplicadas:")
    for i, guideline in enumerate(dynamic_result.guidelines[:3], 1):
        print(f"   {i}. {guideline}")


def demo_validate_prompts():
    """Demuestra validación de configuración de prompts"""
    print_separator("DEMO 6: Validación de Configuración")

    orchestrator = DynamicPromptOrchestrator()
    sectors_to_validate = ["academic_research", "business_analysis", "custom"]

    for sector_id in sectors_to_validate:
        print(f"\n🔍 Validando sector: {sector_id}")

        validation = orchestrator.validate_prompts(sector_id)

        status = "✅ VÁLIDO" if validation['valid'] else "❌ INVÁLIDO"
        print(f"   Estado: {status}")
        print(f"   Score: {validation['score']}/100")

        if validation['issues']:
            print(f"   ⚠️ Problemas:")
            for issue in validation['issues']:
                print(f"      • {issue}")

        if validation['warnings']:
            print(f"   💡 Advertencias:")
            for warning in validation['warnings'][:2]:
                print(f"      • {warning}")


def demo_statistics():
    """Demuestra obtención de estadísticas"""
    print_separator("DEMO 7: Estadísticas del Sistema")

    manager = PromptDesignManager()
    stats = manager.get_statistics()

    print("📊 Estadísticas del Sistema de Prompts:\n")
    print(f"   Sectores Totales: {stats['total_sectors']}")
    print(f"   Sectores Habilitados: {stats['enabled_sectors']}")
    print(f"   Sector Activo: {stats['active_sector_name']} ({stats['active_sector_id']})")
    print(f"   Intent Prompts Totales: {stats['total_intent_prompts']}")
    print(f"   Guidelines Totales: {stats['total_guidelines']}")
    print(f"   Versión: {stats['version']}")
    print(f"   Última Actualización: {stats['last_updated'][:19] if stats['last_updated'] != 'N/A' else 'N/A'}")


def main():
    """Ejecuta todas las demos"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              DEMO: Sistema de Prompt Design Dinámico                     ║
║              Configuración de RAG por Sector/Dominio                     ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")

    # Demos síncronas
    demo_list_sectors()
    demo_change_sector()
    demo_create_custom_sector()
    demo_test_prompts()
    demo_validate_prompts()
    demo_statistics()

    # Demo asíncrona
    print_separator("DEMOS ASÍNCRONAS")
    asyncio.run(demo_with_intent_detection())

    print_separator("DEMO COMPLETADO")
    print("✨ Todas las demos ejecutadas exitosamente!")
    print("\n💡 Próximos pasos:")
    print("   1. Abre la UI de Gradio: python launch_with_api.py")
    print("   2. Ve al tab '🎨 Diseño de Prompts'")
    print("   3. Configura tus sectores personalizados")
    print("   4. Prueba el sistema con diferentes queries\n")


if __name__ == "__main__":
    main()
