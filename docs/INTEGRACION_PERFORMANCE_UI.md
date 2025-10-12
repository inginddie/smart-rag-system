# Integración del Dashboard de Performance en la UI

## Resumen

Se ha integrado exitosamente el sistema de monitoreo de performance en la aplicación RAG, proporcionando:
- ✅ Panel de Performance en Gradio UI
- ✅ API REST con FastAPI para métricas
- ✅ Visualización en tiempo real
- ✅ Gestión de Circuit Breakers

## Componentes Integrados

### 1. Panel de Performance en Gradio (`ui/components/performance_panel.py`)

Panel completo con 6 pestañas:

#### 📈 Métricas Globales
- Total de workflows ejecutados
- Tasa de éxito
- Tiempo promedio de ejecución
- Métricas de performance del sistema

#### 🤖 Agentes
- Métricas detalladas por agente
- Latencia promedio
- Percentiles (P95, P99)
- Tasa de éxito por agente

#### 🔌 Circuit Breakers
- Estado de cada circuit breaker (CLOSED/OPEN/HALF_OPEN)
- Llamadas exitosas/fallidas/rechazadas
- Reset manual de circuit breakers

#### ⚠️ Alertas
- Detección de agentes lentos (configurable)
- Detección de agentes con fallos (configurable)
- Umbrales personalizables

#### ⚖️ Load Balancer
- Estrategia actual de balanceo
- Estadísticas por agente
- Load score y conexiones activas

#### 📋 Reporte JSON
- Reporte completo en formato JSON
- Exportable para análisis externo

### 2. API REST con FastAPI (`src/api/`)

Endpoints disponibles:

```
GET  /api/performance/metrics          - Métricas generales
GET  /api/performance/report           - Reporte completo
GET  /api/performance/agents           - Métricas de todos los agentes
GET  /api/performance/agents/{name}    - Métricas de un agente específico
GET  /api/performance/slow-agents      - Agentes lentos
GET  /api/performance/failing-agents   - Agentes con fallos
GET  /api/performance/circuit-breakers - Estado de circuit breakers
POST /api/performance/circuit-breakers/{name}/reset - Reset de circuit breaker
GET  /api/performance/load-balancer/stats - Estadísticas del load balancer
GET  /api/performance/health           - Health check
```

### 3. Launcher Integrado (`launch_with_api.py`)

Script para ejecutar ambos servicios:

```bash
# Ejecutar UI + API (recomendado)
python launch_with_api.py

# Solo UI (Gradio)
python launch_with_api.py --ui-only

# Solo API (FastAPI)
python launch_with_api.py --api-only

# Puertos personalizados
python launch_with_api.py --gradio-port 7860 --api-port 8000

# Compartir Gradio públicamente
python launch_with_api.py --share
```

## Cómo Usar

### Opción 1: Usar el Panel en Gradio (Recomendado)

1. **Iniciar la aplicación**:
   ```bash
   python launch_with_api.py
   ```

2. **Acceder a Gradio**:
   - Abrir navegador en `http://localhost:7860`
   - Ir a la pestaña "📊 Performance"

3. **Visualizar métricas**:
   - Click en "🔄 Actualizar" en cada sección
   - Las métricas se actualizan en tiempo real

4. **Gestionar Circuit Breakers**:
   - Ver estado en la pestaña "🔌 Circuit Breakers"
   - Resetear manualmente si es necesario

### Opción 2: Usar la API REST

1. **Iniciar la API**:
   ```bash
   python launch_with_api.py --api-only
   ```

2. **Acceder a la documentación**:
   - Abrir `http://localhost:8000/docs`
   - Explorar endpoints interactivos

3. **Consultar métricas**:
   ```bash
   # Métricas globales
   curl http://localhost:8000/api/performance/metrics
   
   # Reporte completo
   curl http://localhost:8000/api/performance/report
   
   # Agentes lentos
   curl http://localhost:8000/api/performance/slow-agents?threshold_ms=5000
   ```

### Opción 3: Usar Ambos (Recomendado para Producción)

```bash
# Iniciar ambos servicios
python launch_with_api.py

# Acceder a:
# - Gradio UI: http://localhost:7860
# - FastAPI: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## Flujo de Trabajo Típico

### 1. Monitoreo Continuo

```
1. Abrir Gradio en http://localhost:7860
2. Ir a pestaña "📊 Performance"
3. Revisar "📈 Métricas Globales"
4. Verificar que success_rate > 95%
5. Revisar "⚠️ Alertas" para problemas
```

### 2. Detección de Problemas

```
1. Si hay alertas de agentes lentos:
   - Ir a "🤖 Agentes"
   - Identificar agente problemático
   - Revisar latencia y percentiles

2. Si hay circuit breakers abiertos:
   - Ir a "🔌 Circuit Breakers"
   - Ver estado y métricas
   - Investigar causa del problema
   - Resetear cuando esté resuelto
```

### 3. Análisis de Performance

```
1. Ir a "📋 Reporte JSON"
2. Generar reporte completo
3. Copiar JSON para análisis
4. Usar herramientas externas si es necesario
```

## Ejemplos de Uso

### Ejemplo 1: Verificar Salud del Sistema

```python
import requests

# Verificar health
response = requests.get('http://localhost:8000/api/performance/health')
data = response.json()

if data['status'] == 'healthy':
    print("✅ Sistema saludable")
else:
    print(f"⚠️ Sistema degradado: {data}")
```

### Ejemplo 2: Monitorear Agentes Lentos

```python
import requests

# Obtener agentes lentos (> 3 segundos)
response = requests.get(
    'http://localhost:8000/api/performance/slow-agents',
    params={'threshold_ms': 3000}
)
data = response.json()

if data['data']['count'] > 0:
    print(f"⚠️ {data['data']['count']} agentes lentos detectados:")
    for agent in data['data']['slow_agents']:
        print(f"  - {agent['agent_name']}: {agent['avg_duration_ms']:.0f}ms")
```

### Ejemplo 3: Resetear Circuit Breaker

```python
import requests

# Resetear circuit breaker de un agente
agent_name = "QueryAgent"
response = requests.post(
    f'http://localhost:8000/api/performance/circuit-breakers/{agent_name}/reset'
)
data = response.json()

print(data['message'])
```

## Interpretación de Métricas

### Estados de Circuit Breaker

| Estado | Emoji | Significado | Acción |
|--------|-------|-------------|--------|
| CLOSED | ✅ | Normal | Ninguna |
| HALF_OPEN | 🟡 | Recuperándose | Monitorear |
| OPEN | 🔴 | Bloqueado | Investigar y resetear |

### Umbrales Recomendados

| Métrica | Umbral | Acción si se excede |
|---------|--------|---------------------|
| Success Rate | < 95% | Investigar fallos |
| Latencia Promedio | > 5000ms | Optimizar agente |
| Tasa de Fallos | > 10% | Revisar logs |
| P99 Latency | > 10000ms | Revisar casos extremos |

### Colores en el UI

- 🟢 **Verde**: Todo normal (success rate > 95%)
- 🟡 **Amarillo**: Degradado (success rate 80-95%)
- 🔴 **Rojo**: Crítico (success rate < 80%)

## Troubleshooting

### Problema: "Workflow engine not initialized"

**Solución**:
```python
# En launch_with_api.py, asegurarse de que se llama:
initialize_workflow_engine()
```

### Problema: Panel de Performance vacío

**Causa**: No hay métricas generadas aún

**Solución**:
1. Ejecutar algunas consultas en el chat
2. Esperar a que se generen métricas
3. Actualizar el panel

### Problema: API no responde

**Verificar**:
```bash
# Verificar que FastAPI está corriendo
curl http://localhost:8000/health

# Ver logs
# Los logs mostrarán si hay errores
```

### Problema: Circuit Breaker siempre OPEN

**Causa**: Agente fallando repetidamente

**Solución**:
1. Revisar logs del agente
2. Corregir problema subyacente
3. Resetear circuit breaker manualmente

## Configuración Avanzada

### Cambiar Umbrales de Circuit Breaker

En `src/agents/orchestration/circuit_breaker.py`:

```python
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5  # Cambiar según necesidad
    success_threshold: int = 2
    timeout: float = 60.0
    slow_call_threshold: float = 10.0
```

### Cambiar Estrategia de Load Balancer

```python
from src.agents.orchestration import LoadBalancingStrategy

# En el código
workflow_engine.load_balancer.change_strategy(
    LoadBalancingStrategy.LEAST_CONNECTIONS
)
```

### Ajustar Intervalo de Auto-refresh

En `ui/components/performance_panel.py`, modificar el comentario sobre auto-refresh para implementarlo si se desea.

## Mejores Prácticas

1. **Monitoreo Regular**: Revisar métricas al menos una vez al día
2. **Alertas Proactivas**: Configurar umbrales conservadores
3. **Documentar Incidentes**: Registrar cuando se resetean circuit breakers
4. **Análisis de Tendencias**: Exportar reportes JSON periódicamente
5. **Optimización Continua**: Ajustar umbrales basado en datos reales

## Próximos Pasos

- [ ] Agregar exportación de métricas a Prometheus
- [ ] Implementar alertas por email/Slack
- [ ] Crear dashboards en Grafana
- [ ] Agregar predicción de problemas con ML
- [ ] Implementar auto-scaling basado en métricas

## Soporte

Para problemas o preguntas:
1. Revisar logs en `logs/app.log`
2. Consultar documentación en `docs/PERFORMANCE_UI_GUIDE.md`
3. Verificar tests en `tests/agents/test_performance_optimization.py`

---

**Fecha de integración**: 2025-10-11
**Versión**: 1.0.0
**Estado**: ✅ Completamente integrado y funcional
