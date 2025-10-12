# Guía de Visualización de Performance

## Descripción General

El sistema de performance incluye un dashboard completo para monitorear en tiempo real el estado de los agentes y el sistema de orquestación.

## Componentes de Visualización

### 1. API Endpoints

Los siguientes endpoints están disponibles para obtener métricas:

#### Métricas Generales
```
GET /api/performance/metrics
```
Retorna métricas generales del workflow engine.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "total_workflows": 150,
    "successful_workflows": 145,
    "avg_execution_time_ms": 1250.5,
    "circuit_breaker_metrics": {...},
    "load_balancer_metrics": {...},
    "performance_metrics": {...}
  }
}
```

#### Reporte Completo
```
GET /api/performance/report
```
Genera un reporte completo con todas las métricas.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "workflow_metrics": {...},
    "performance_report": {
      "global_metrics": {
        "total_requests": 1000,
        "success_rate": 0.95,
        "avg_duration_ms": 150.5,
        "throughput_per_second": 10.5
      },
      "agent_metrics": {
        "AgentName": {
          "total_requests": 100,
          "success_rate": 0.98,
          "avg_duration_ms": 120.0,
          "p50_duration_ms": 100.0,
          "p95_duration_ms": 200.0,
          "p99_duration_ms": 300.0
        }
      },
      "slow_agents": [...],
      "failing_agents": [...]
    }
  }
}
```

#### Métricas por Agente
```
GET /api/performance/agents/{agent_name}
```
Obtiene métricas detalladas de un agente específico.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "agent_name": "AgentName",
    "performance": {
      "total_requests": 100,
      "success_rate": 0.98,
      "avg_duration_ms": 120.0,
      "p95_duration_ms": 200.0
    },
    "load_balancer": {
      "active_connections": 2,
      "load_score": 0.5
    },
    "circuit_breaker": {
      "state": "closed",
      "failure_count": 0
    }
  }
}
```

#### Agentes Lentos
```
GET /api/performance/slow-agents?threshold_ms=5000
```
Obtiene lista de agentes con latencia alta.

#### Agentes con Fallos
```
GET /api/performance/failing-agents?threshold_rate=0.1
```
Obtiene lista de agentes con alta tasa de fallos.

#### Estado de Circuit Breakers
```
GET /api/performance/circuit-breakers
```
Obtiene estado de todos los circuit breakers.

#### Reset de Circuit Breaker
```
POST /api/performance/circuit-breakers/{agent_name}/reset
```
Resetea manualmente un circuit breaker.

#### Health Check
```
GET /api/performance/health
```
Verifica el estado de salud del sistema.

**Respuesta:**
```json
{
  "status": "healthy",
  "data": {
    "success_rate": 0.95,
    "slow_agents_count": 0,
    "failing_agents_count": 0,
    "total_requests": 1000,
    "uptime_seconds": 3600
  }
}
```

### 2. Dashboard React

El componente `PerformanceDashboard.tsx` proporciona una interfaz visual completa.

#### Características:

1. **Métricas Globales (Cards superiores)**
   - Total de requests
   - Tasa de éxito
   - Latencia promedio
   - Throughput (requests/segundo)

2. **Alertas**
   - Agentes lentos detectados
   - Agentes con fallos detectados

3. **Tabla de Agentes**
   - Nombre del agente
   - Número de requests
   - Tasa de éxito
   - Latencia promedio
   - Percentiles P95 y P99
   - Estado (Healthy/Degraded/Failing)

4. **Circuit Breakers**
   - Estado por agente (CLOSED/OPEN/HALF_OPEN)
   - Llamadas exitosas/fallidas/rechazadas
   - Botón de reset manual

5. **Auto-refresh**
   - Actualización automática cada 5 segundos
   - Toggle para activar/desactivar

## Integración en tu Aplicación

### Paso 1: Registrar las rutas API

En tu archivo `main.py` o `app.py`:

```python
from fastapi import FastAPI
from src.api.performance_routes import router as performance_router, set_workflow_engine
from src.agents.orchestration import WorkflowEngine

app = FastAPI()

# Inicializar workflow engine
workflow_engine = WorkflowEngine()

# Configurar el engine en las rutas
set_workflow_engine(workflow_engine)

# Registrar rutas
app.include_router(performance_router)
```

### Paso 2: Agregar el componente React

En tu aplicación React, importa y usa el componente:

```tsx
import PerformanceDashboard from './components/PerformanceDashboard';

function App() {
  return (
    <div>
      <PerformanceDashboard />
    </div>
  );
}
```

### Paso 3: Configurar dependencias

Asegúrate de tener instaladas las dependencias necesarias:

```bash
# Backend
pip install fastapi uvicorn

# Frontend
npm install lucide-react
# O si usas shadcn/ui:
npx shadcn-ui@latest add card badge button alert
```

## Ejemplos de Uso

### Monitoreo en Tiempo Real

```typescript
// Obtener métricas cada 5 segundos
setInterval(async () => {
  const response = await fetch('/api/performance/metrics');
  const data = await response.json();
  console.log('Current metrics:', data);
}, 5000);
```

### Detectar Problemas

```typescript
// Verificar agentes lentos
const response = await fetch('/api/performance/slow-agents?threshold_ms=3000');
const data = await response.json();

if (data.data.count > 0) {
  console.warn('Slow agents detected:', data.data.slow_agents);
  // Enviar alerta, notificación, etc.
}
```

### Reset de Circuit Breaker

```typescript
// Resetear un circuit breaker manualmente
async function resetAgent(agentName: string) {
  const response = await fetch(
    `/api/performance/circuit-breakers/${agentName}/reset`,
    { method: 'POST' }
  );
  const data = await response.json();
  console.log('Circuit breaker reset:', data);
}
```

## Visualización de Métricas

### Interpretación de Colores

- 🟢 **Verde (Healthy)**: Success rate > 95%
- 🟡 **Amarillo (Degraded)**: Success rate 80-95%
- 🔴 **Rojo (Failing)**: Success rate < 80%

### Estados de Circuit Breaker

- **CLOSED** (Verde): Operación normal
- **HALF_OPEN** (Amarillo): Probando recuperación
- **OPEN** (Rojo): Bloqueando requests

### Umbrales Recomendados

- **Latencia lenta**: > 5000ms
- **Tasa de fallos alta**: > 10%
- **Success rate mínimo**: 95%

## Personalización

### Cambiar Intervalo de Refresh

En `PerformanceDashboard.tsx`:

```typescript
// Cambiar de 5000ms a 10000ms (10 segundos)
const interval = setInterval(fetchReport, 10000);
```

### Ajustar Umbrales

En las llamadas API:

```typescript
// Agentes lentos con umbral de 3 segundos
fetch('/api/performance/slow-agents?threshold_ms=3000')

// Agentes con > 5% de fallos
fetch('/api/performance/failing-agents?threshold_rate=0.05')
```

### Agregar Gráficos

Puedes integrar librerías como Chart.js o Recharts:

```typescript
import { LineChart, Line, XAxis, YAxis } from 'recharts';

// Graficar latencia en el tiempo
<LineChart data={latencyData}>
  <Line type="monotone" dataKey="latency" stroke="#8884d8" />
  <XAxis dataKey="timestamp" />
  <YAxis />
</LineChart>
```

## Troubleshooting

### Error: "Workflow engine not initialized"

Asegúrate de llamar `set_workflow_engine(engine)` antes de usar las rutas.

### Dashboard no actualiza

Verifica que el auto-refresh esté activado y que el backend esté respondiendo.

### Métricas vacías

Ejecuta algunas queries para generar métricas iniciales.

## Mejores Prácticas

1. **Monitoreo Continuo**: Mantén el dashboard abierto durante operaciones críticas
2. **Alertas Proactivas**: Configura alertas para agentes lentos/fallidos
3. **Reset Cuidadoso**: Solo resetea circuit breakers después de verificar que el problema está resuelto
4. **Análisis de Tendencias**: Revisa percentiles P95/P99 para identificar problemas de latencia
5. **Documentación**: Documenta patrones de comportamiento normal para tu sistema

## Próximos Pasos

- Agregar exportación de métricas a Prometheus/Grafana
- Implementar alertas por email/Slack
- Crear dashboards personalizados por equipo
- Agregar predicción de problemas con ML
