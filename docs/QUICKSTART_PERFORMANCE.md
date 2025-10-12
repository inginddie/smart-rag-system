# 🚀 Inicio Rápido - Dashboard de Performance

## Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.template .env
# Editar .env y agregar tu OPENAI_API_KEY
```

## Ejecución

### Opción 1: UI + API (Recomendado)

```bash
python launch_with_api.py
```

Acceder a:
- **Gradio UI**: http://localhost:7860
- **Performance API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Opción 2: Solo UI

```bash
python launch_with_api.py --ui-only
```

### Opción 3: Solo API

```bash
python launch_with_api.py --api-only
```

## Uso del Dashboard

### 1. Abrir Gradio

```
http://localhost:7860
```

### 2. Ir a la pestaña "📊 Performance"

Verás 6 secciones:
- 📈 **Métricas Globales**: Overview del sistema
- 🤖 **Agentes**: Performance por agente
- 🔌 **Circuit Breakers**: Estado de protección
- ⚠️ **Alertas**: Agentes lentos o con fallos
- ⚖️ **Load Balancer**: Distribución de carga
- 📋 **Reporte JSON**: Exportación completa

### 3. Actualizar Métricas

Click en "🔄 Actualizar" en cada sección para ver datos en tiempo real.

## Uso de la API

### Obtener Métricas

```bash
# Métricas globales
curl http://localhost:8000/api/performance/metrics

# Reporte completo
curl http://localhost:8000/api/performance/report

# Agentes lentos (> 5 segundos)
curl http://localhost:8000/api/performance/slow-agents?threshold_ms=5000

# Health check
curl http://localhost:8000/api/performance/health
```

### Resetear Circuit Breaker

```bash
curl -X POST http://localhost:8000/api/performance/circuit-breakers/AgentName/reset
```

## Interpretación Rápida

### Estados de Circuit Breaker

- ✅ **CLOSED**: Todo bien
- 🟡 **HALF_OPEN**: Recuperándose
- 🔴 **OPEN**: Bloqueado (requiere atención)

### Métricas Clave

| Métrica | Bueno | Atención | Crítico |
|---------|-------|----------|---------|
| Success Rate | > 95% | 80-95% | < 80% |
| Latencia | < 2s | 2-5s | > 5s |
| Tasa de Fallos | < 5% | 5-10% | > 10% |

## Troubleshooting

### No hay métricas

**Solución**: Ejecuta algunas consultas en el chat primero.

### Circuit Breaker OPEN

**Solución**:
1. Revisar logs
2. Corregir problema
3. Resetear manualmente

### API no responde

**Verificar**:
```bash
curl http://localhost:8000/health
```

## Documentación Completa

- **Guía de Performance**: `docs/PERFORMANCE_UI_GUIDE.md`
- **Integración**: `docs/INTEGRACION_PERFORMANCE_UI.md`
- **Tarea Completada**: `HU5_TAREA_5.3_COMPLETADA.md`

## Tests

```bash
# Ejecutar tests de performance
pytest tests/agents/test_performance_optimization.py -v

# Todos los tests de orquestación
pytest tests/agents/test_workflow.py tests/agents/test_orchestrator.py tests/agents/test_performance_optimization.py -v
```

## Soporte

Para más información, consulta la documentación completa en `docs/`.

---

**¿Listo para empezar?** 🎉

```bash
python launch_with_api.py
```

Luego abre http://localhost:7860 y ve a la pestaña "📊 Performance"
