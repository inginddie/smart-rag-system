# -*- coding: utf-8 -*-
"""
Utilidades para manejo limpio de imports opcionales
"""
import importlib
from typing import Any, Dict, List, Optional, Tuple, Union
import warnings


class OptionalImportManager:
    """Manejador centralizado para imports opcionales"""
    
    def __init__(self):
        self._cache = {}
        self._missing_deps = set()
    
    def try_import(self, 
                   module_name: str, 
                   package: Optional[str] = None,
                   error_message: Optional[str] = None) -> Tuple[Any, bool]:
        """
        Intenta importar un módulo y devuelve (module, success)
        
        Args:
            module_name: Nombre del módulo a importar
            package: Paquete padre (opcional)
            error_message: Mensaje personalizado de error
            
        Returns:
            Tuple[módulo_o_None, éxito_booleano]
        """
        cache_key = f"{package}.{module_name}" if package else module_name
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            if package:
                module = importlib.import_module(module_name, package)
            else:
                module = importlib.import_module(module_name)
            
            self._cache[cache_key] = (module, True)
            return module, True
            
        except ImportError as e:
            self._missing_deps.add(cache_key)
            if error_message:
                warnings.warn(f"Optional dependency missing: {error_message}")
            
            self._cache[cache_key] = (None, False)
            return None, False
    
    def require_import(self, 
                      module_name: str, 
                      package: Optional[str] = None,
                      install_hint: Optional[str] = None) -> Any:
        """
        Importa un módulo requerido o lanza excepción informativa
        
        Args:
            module_name: Nombre del módulo
            package: Paquete padre (opcional)  
            install_hint: Comando de instalación sugerido
            
        Returns:
            El módulo importado
            
        Raises:
            ImportError: Con mensaje informativo si falla
        """
        module, success = self.try_import(module_name, package)
        
        if not success:
            install_msg = f"\n\nInstalación: {install_hint}" if install_hint else ""
            raise ImportError(
                f"Required dependency '{module_name}' not found.{install_msg}"
            )
        
        return module
    
    def check_dependencies(self, deps: List[Dict[str, str]]) -> Dict[str, bool]:
        """
        Verifica múltiples dependencias de una vez
        
        Args:
            deps: Lista de dict con keys: 'name', 'package'?, 'install_hint'?
            
        Returns:
            Dict con nombre -> disponible (bool)
        """
        results = {}
        
        for dep in deps:
            name = dep['name']
            package = dep.get('package')
            _, available = self.try_import(name, package)
            results[name] = available
        
        return results
    
    def get_missing_deps(self) -> List[str]:
        """Devuelve lista de dependencias faltantes"""
        return list(self._missing_deps)
    
    def create_fallback_class(self, 
                            class_name: str, 
                            methods: Optional[Dict[str, Any]] = None) -> type:
        """
        Crea una clase fallback cuando una dependencia no está disponible
        
        Args:
            class_name: Nombre de la clase
            methods: Dict con métodos a implementar como fallbacks
            
        Returns:
            Clase fallback
        """
        def __init__(self, *args, **kwargs):
            raise ImportError(
                f"Cannot use {class_name}: required dependencies not installed"
            )
        
        attrs = {'__init__': __init__}
        if methods:
            attrs.update(methods)
        
        return type(class_name, (), attrs)


# Instancia global para uso en todo el proyecto
import_manager = OptionalImportManager()


# Shortcuts útiles para casos comunes
def try_import_langchain():
    """Intenta importar componentes de LangChain"""
    deps = [
        {'name': 'langchain_community.document_loaders', 'install_hint': 'pip install langchain-community'},
        {'name': 'langchain.text_splitter', 'install_hint': 'pip install langchain'},
        {'name': 'langchain.schema', 'install_hint': 'pip install langchain'},
    ]
    
    return import_manager.check_dependencies(deps)


def try_import_optional_deps():
    """Verifica dependencias opcionales comunes del proyecto"""
    deps = [
        {'name': 'pandas', 'install_hint': 'pip install pandas'},
        {'name': 'psycopg2', 'install_hint': 'pip install psycopg2-binary'},
        {'name': 'redis', 'install_hint': 'pip install redis'},
        {'name': 'openpyxl', 'install_hint': 'pip install openpyxl'},
    ]
    
    return import_manager.check_dependencies(deps)


def get_dependency_report() -> str:
    """Genera reporte del estado de dependencias"""
    langchain_deps = try_import_langchain()
    optional_deps = try_import_optional_deps()
    
    report = ["📦 **Reporte de Dependencias**\n"]
    
    # LangChain (core)
    report.append("**Core Dependencies:**")
    for dep, available in langchain_deps.items():
        status = "✅" if available else "❌"
        report.append(f"- {dep}: {status}")
    
    # Opcionales
    report.append("\n**Optional Dependencies:**")
    for dep, available in optional_deps.items():
        status = "✅" if available else "⚠️"
        report.append(f"- {dep}: {status}")
    
    missing = import_manager.get_missing_deps()
    if missing:
        report.append(f"\n**Missing:** {len(missing)} dependencies")
    
    return "\n".join(report) 