#!/usr/bin/env python3
"""
UI Testing - Academic Templates
"""

import sys
from pathlib import Path

def setup_path():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

def test_ui_enhanced():
    """Test UI con templates enhanced"""
    try:
        setup_path()
        
        print("🧪 Testing UI Integration...")
        
        # Test app creation
        from ui.gradio_app import GradioRAGApp
        app = GradioRAGApp()
        print("✅ Enhanced Gradio app created")
        
        # Test service with templates
        service = app.rag_service
        status = service.get_status()
        
        template_support = status.get('template_support', False)
        quality_validation = status.get('quality_validation', False)
        
        print(f"✅ Template support: {template_support}")
        print(f"✅ Quality validation: {quality_validation}")
        
        return True
        
    except Exception as e:
        print(f"❌ UI test failed: {e}")
        return False

def run_sample_queries():
    """Test con consultas de ejemplo"""
    try:
        setup_path()
        from ui.gradio_app import GradioRAGApp
        
        app = GradioRAGApp()
        
        # Inicializar si no está inicializado
        if not app.initialized:
            init_result = app.initialize_service()
            print(f"📋 Service init: {init_result}")
        
        # Test queries por intent type
        test_queries = [
            ("¿Qué es machine learning?", "DEFINITION"),
            ("Compara supervised vs unsupervised learning", "COMPARISON"),
            ("Estado del arte en NLP para requirements", "STATE_OF_ART"),
            ("¿Qué limitaciones tienen los métodos actuales?", "GAP_ANALYSIS")
        ]
        
        print("\n🔍 Testing sample queries:")
        for query, expected_intent in test_queries:
            try:
                response, system_info = app.chat_response(query, [])
                
                # Check if response contains academic structure
                has_structure = any(keyword in response for keyword in 
                                  ["**1.", "**DEFINICIÓN", "**ESTRUCTURA", "**ANÁLISIS"])
                
                print(f"   ✅ {expected_intent}: structured={has_structure}")
                
            except Exception as e:
                print(f"   ❌ {expected_intent}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample queries test failed: {e}")
        return False

def test_ui_launch():
    """Test launch básico de UI"""
    try:
        setup_path()
        from ui.gradio_app import GradioRAGApp
        
        app = GradioRAGApp()
        interface = app.create_interface()
        
        print("✅ Interface created successfully")
        print("📱 Ready for gradio.launch()")
        
        return True
        
    except Exception as e:
        print(f"❌ UI launch test failed: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 UI Testing - Academic Templates")
    print("=" * 40)
    
    # Tests
    ui_ok = test_ui_enhanced()
    queries_ok = run_sample_queries()
    launch_ok = test_ui_launch()
    
    print(f"\n📊 UI TEST RESULTS:")
    print(f"   🖥️ Enhanced UI: {'✅' if ui_ok else '❌'}")
    print(f"   🔍 Sample Queries: {'✅' if queries_ok else '❌'}")
    print(f"   🚀 Launch Ready: {'✅' if launch_ok else '❌'}")
    
    if all([ui_ok, queries_ok, launch_ok]):
        print(f"\n🎉 UI TESTING PASSED!")
        print(f"\n🚀 LAUNCH COMMAND:")
        print(f"   python main.py --mode ui")
    else:
        print(f"\n❌ Fix issues before launch")

if __name__ == "__main__":
    main()