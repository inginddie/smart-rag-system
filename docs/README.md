# Documentación del Sistema RAG

## 📚 Índice de Documentación

### 🚀 Para Empezar
1. **[QUICKSTART_PERFORMANCE.md](QUICKSTART_PERFORMANCE.md)** - Inicio rápido (5 minutos)
   - Instalación
   - Ejecución
   - Uso básico del dashboard

### 📖 Documentación Principal
2. **[HU5_SISTEMA_ORQUESTACION_COMPLETO.md](HU5_SISTEMA_ORQUESTACION_COMPLETO.md)** - Documentación completa
   - Sistema de orquestación multi-agente
   - Componentes de performance
   - Dashboard de visualización
   - Guías de uso completas

3. **[RESUMEN_FINAL_HU5.md](RESUMEN_FINAL_HU5.md)** - Resumen ejecutivo
   - Componentes implementados
   - Archivos creados/modificados
   - Tests y verificaciones
   - Estado del proyecto

### 🎯 Guías Específicas
4. **[PERFORMANCE_UI_GUIDE.md](PERFORMANCE_UI_GUIDE.md)** - Guía completa del dashboard
   - Descripción de endpoints API
   - Uso del dashboard React
   - Ejemplos de uso
   - Troubleshooting

5. **[INTEGRACION_PERFORMANCE_UI.md](INTEGRACION_PERFORMANCE_UI.md)** - Documentación técnica
   - Integración en la aplicación
   - Flujo de trabajo típico
   - Configuración avanzada
   - Mejores prácticas

6. **[DEMO_PERFORMANCE_DASHBOARD.md](DEMO_PERFORMANCE_DASHBOARD.md)** - Demo funcional
   - Estado actual del sistema
   - Endpoints verificados
   - Cómo usar el dashboard
   - Comandos útiles

---

## 🎯 Rutas Rápidas

### Para Desarrolladores
- **Arquitectura**: Ver `HU5_SISTEMA_ORQUESTACION_COMPLETO.md` → Sección "Componentes Implementados"
- **API REST**: Ver `PERFORMANCE_UI_GUIDE.md` → Sección "API Endpoints"
- **Tests**: Ver `RESUMEN_FINAL_HU5.md` → Sección "Tests"

### Para Usuarios
- **Inicio Rápido**: `QUICKSTART_PERFORMANCE.md`
- **Uso del Dashboard**: `PERFORMANCE_UI_GUIDE.md` → Sección "Dashboard React"
- **Troubleshooting**: `INTEGRACION_PERFORMANCE_UI.md` → Sección "Troubleshooting"

### Para Operaciones
- **Monitoreo**: `PERFORMANCE_UI_GUIDE.md` → Sección "Ejemplos de Uso"
- **Alertas**: `INTEGRACION_PERFORMANCE_UI.md` → Sección "Flujo de Trabajo"
- **Configuración**: `HU5_SISTEMA_ORQUESTACION_COMPLETO.md` → Sección "Configuración"

---

## 📂 Estructura de Documentación

```
docs/
├── README.md                              (Este archivo - Índice)
├── QUICKSTART_PERFORMANCE.md              (Inicio rápido)
├── HU5_SISTEMA_ORQUESTACION_COMPLETO.md  (Documentación completa)
├── RESUMEN_FINAL_HU5.md                  (Resumen ejecutivo)
├── PERFORMANCE_UI_GUIDE.md               (Guía del dashboard)
├── INTEGRACION_PERFORMANCE_UI.md         (Documentación técnica)
├── DEMO_PERFORMANCE_DASHBOARD.md         (Demo funcional)
├── development/                           (Guías de desarrollo)
├── guides/                                (Guías de usuario)
└── technical/                             (Documentación técnica)
```

---

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar aplicación
python launch_with_api.py

# 3. Acceder a:
# - Gradio: http://localhost:7860
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
```

---

## 📞 Soporte

- **README Principal**: Ver `../README.md` en la raíz del proyecto
- **Tests**: `pytest tests/agents/ -v`
- **Logs**: `logs/app.log`

---

**Última actualización**: 2025-10-11
