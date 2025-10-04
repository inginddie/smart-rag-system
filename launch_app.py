# -*- coding: utf-8 -*-
"""
Script para lanzar la aplicación Gradio RAG con panel de administración de keywords
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.gradio_app import GradioRAGApp

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando Sistema RAG con Administración de Keywords")
    print("=" * 60)
    print()
    
    app = GradioRAGApp()
    
    # Configuración de lanzamiento
    # Usar None para que Gradio encuentre un puerto libre automáticamente
    launch_config = {
        'server_port': None,  # Gradio encontrará un puerto libre
        'share': False,
        'show_error': True,
        'quiet': False,
        'inbrowser': True  # Abrir automáticamente en el navegador
    }
    
    print(f"📡 Servidor iniciando (buscando puerto libre)...")
    print(f"🌐 La URL se mostrará cuando el servidor esté listo")
    print()
    print("💡 Pasos para usar el panel de administración:")
    print("   1. Ve al tab '⚙️ Administración'")
    print("   2. Presiona '🚀 Inicializar Sistema'")
    print("   3. Ve al tab '🔧 Administración' (nuevo)")
    print("   4. ¡Gestiona keywords dinámicamente!")
    print()
    print("=" * 60)
    print()
    
    try:
        app.launch(**launch_config)
    except KeyboardInterrupt:
        print("\n\n👋 Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
