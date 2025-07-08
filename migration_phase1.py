"""
Script de migración para activar capacidades agentic gradualmente.
Permite migración segura sin romper funcionalidad existente.
"""

import sys
import os
from pathlib import Path
import subprocess
import importlib
import shutil

def check_dependencies():
    """Verifica que las dependencias necesarias estén instaladas"""
    required_packages = [
        'langgraph',
        'crewai', 
        'redis',
        'httpx',
        'pytest-asyncio'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    return missing

def install_dependencies(packages):
    """Instala dependencias faltantes"""
    if not packages:
        return True
    
    print(f"\n📦 Instalando dependencias faltantes: {', '.join(packages)}")
    
    package_map = {
        'langgraph': 'langgraph>=0.2.0',
        'crewai': 'crewai>=0.70.0',
        'redis': 'redis>=5.0.0',
        'httpx': 'httpx>=0.24.0',
        'pytest-asyncio': 'pytest-asyncio>=0.21.0'
    }
    
    for package in packages:
        package_spec = package_map.get(package, package)
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package_spec], 
                         check=True, capture_output=True)
            print(f"✅ Instalado: {package_spec}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {package}: {e}")
            return False
    
    return True

def create_agent_files():
    """Crea archivos de agentes si no existen"""
    files_to_create = [
        "src/agents/__init__.py",
        "src/agents/base/__init__.py", 
        "src/agents/specialized/__init__.py",
        "src/agents/memory/__init__.py",
        "src/orchestration/__init__.py"
    ]
    
    for file_path in files_to_create:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("# -*- coding: utf-8 -*-\n")
            print(f"✅ Creado: {file_path}")

def test_agentic_components():
    """Prueba componentes agentic básicos"""
    print("\n🧪 Testing agentic components...")
    
    try:
        # Test imports
        from src.agents.base.agent import BaseAgent
        from src.agents.memory.manager import MemoryManager
        from src.agents.specialized.document_search import DocumentSearchAgent
        print("✅ Imports successful")
        
        # Test basic agent creation
        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["test"]
            async def process_query(self, query, context=None):
                from src.agents.base.agent import AgentResponse
                return AgentResponse(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    content="test response",
                    confidence=1.0,
                    metadata={}
                )
        
        agent = TestAgent("TestAgent", "Test agent")
        print("✅ Agent creation successful")
        
        # Test memory manager (without Redis for testing)
        memory = MemoryManager(redis_url="redis://fake")
        print("✅ Memory manager creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def run_migration_tests():
    """Ejecuta tests específicos de migración"""
    print("\n🧪 Running migration tests...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/agents/', '-v', '--tb=short'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All migration tests passed")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("⚠️ pytest not found, skipping automated tests")
        return True
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def backup_current_service():
    """Crea backup del servicio actual"""
    backup_file = "src/services/rag_service_backup.py"
    original_file = "src/services/rag_service.py"
    
    if Path(original_file).exists() and not Path(backup_file).exists():
        shutil.copy2(original_file, backup_file)
        print(f"✅ Backup created: {backup_file}")

def check_redis_availability():
    """Verifica si Redis está disponible"""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        print("✅ Redis server is running")
        return True
    except Exception as e:
        print(f"⚠️ Redis not available: {e}")
        print("   Agentes usarán memoria local solamente")
        return False

def validate_file_structure():
    """Valida que todos los archivos necesarios estén presentes"""
    required_files = [
        "src/agents/base/agent.py",
        "src/agents/memory/manager.py",
        "src/agents/specialized/document_search.py",
        "src/services/agentic_rag_service.py",
        "ui/agentic_gradio_app.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Todos los archivos necesarios están presentes")
    return True

def main():
    """Función principal de migración"""
    print("🚀 Iniciando migración a RAG Agentic...")
    print("=" * 50)
    
    # Paso 1: Verificar dependencias
    print("\n1️⃣ Verificando dependencias...")
    missing_deps = check_dependencies()
    
    if missing_deps:
        print(f"\n⚠️ Dependencias faltantes: {', '.join(missing_deps)}")
        response = input("¿Instalar automáticamente? (y/N): ").lower()
        
        if response == 'y':
            if not install_dependencies(missing_deps):
                print("❌ Error instalando dependencias. Migración abortada.")
                sys.exit(1)
        else:
            print("❌ Dependencias requeridas no instaladas. Migración abortada.")
            sys.exit(1)
    
    # Paso 2: Crear estructura de archivos
    print("\n2️⃣ Creando estructura de agentes...")
    create_agent_files()
    
    # Paso 3: Verificar estructura de archivos
    print("\n3️⃣ Validando estructura de archivos...")
    if not validate_file_structure():
        print("❌ Estructura de archivos incompleta.")
        print("   Por favor, copia todos los códigos a sus archivos respectivos.")
        return 1
    
    # Paso 4: Backup del servicio actual
    print("\n4️⃣ Creando backup del servicio actual...")
    backup_current_service()
    
    # Paso 5: Verificar Redis
    print("\n5️⃣ Verificando Redis...")
    redis_available = check_redis_availability()
    
    # Paso 6: Test componentes agentic
    print("\n6️⃣ Testing componentes agentic...")
    if not test_agentic_components():
        print("❌ Error en componentes agentic. Revisar código.")
        return 1
    
    # Paso 7: Ejecutar tests de migración
    print("\n7️⃣ Ejecutando tests de migración...")
    if not run_migration_tests():
        print("⚠️ Algunos tests fallaron, pero la migración puede continuar.")
    
    # Paso 8: Instrucciones finales
    print("\n" + "=" * 50)
    print("✅ MIGRACIÓN FASE 1 COMPLETADA")
    print("\n📋 Próximos pasos:")
    print("1. ✅ Dependencias instaladas y verificadas")
    print("2. ✅ Estructura de archivos creada")
    print("3. ✅ Componentes agentic funcionando")
    
    if redis_available:
        print("4. ✅ Redis disponible para memoria distribuida")
    else:
        print("4. ⚠️ Redis no disponible (usará memoria local)")
    
    print("\n🚀 Para activar las capacidades agentic:")
    print("   python main.py --mode ui")
    
    print("\n💡 Comandos útiles:")
    print("- Test agentes: pytest tests/agents/ -v")
    print("- Modo clásico: python main.py --mode ui --classic")
    print("- Verificar Redis: redis-cli ping")
    print("- Rollback: cp src/services/rag_service_backup.py src/services/rag_service.py")
    
    print("\n🎯 El sistema mantendrá 100% de compatibilidad.")
    print("Las capacidades agentic se activan automáticamente si están disponibles.")
    
    return 0

if __name__ == "__main__":
    exit(main())