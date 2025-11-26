# 🚀 Guía Rápida: Sistema de Prompts Dinámicos

## 5 Minutos para Empezar

### ¿Qué es esto?

Transforma tu RAG de un sistema académico especializado a un **RAG configurable para cualquier sector** sin tocar código.

### Antes vs Ahora

| Antes | Ahora |
|-------|-------|
| ❌ Hardcoded para investigación académica | ✅ Configurable para cualquier dominio |
| ❌ Cambios requieren código | ✅ Todo desde la UI |
| ❌ Un solo comportamiento | ✅ Múltiples sectores simultáneos |

---

## Paso 1: Lanzar (30 segundos)

```bash
python launch_with_api.py
```

Abrir: `http://localhost:7860`

---

## Paso 2: Ver Sectores Disponibles (1 minuto)

1. Click en tab **🎨 Diseño de Prompts**
2. Verás el sector activo actual
3. En el dropdown hay 6 sectores preconfigur ados:

| Sector | Para qué sirve |
|--------|----------------|
| 🎓 Investigación Académica | Papers, síntesis académica |
| 💼 Análisis de Negocios | Estrategia, ROI, mercado |
| ⚖️ Revisión Legal | Contratos, compliance |
| 🏥 Análisis Médico | Literatura clínica |
| 💻 Documentación Técnica | Arquitectura, código |
| ✨ Personalizado | Tu sector custom |

---

## Paso 3: Cambiar de Sector (30 segundos)

1. En dropdown "Sector Activo", selecciona: **Análisis de Negocios**
2. Click **✅ Activar Sector Seleccionado**
3. Verás confirmación: "✅ Sector activado exitosamente"

---

## Paso 4: Probar el Cambio (1 minuto)

1. Ve a tab **💬 Chat Académico**
2. Pregunta: *"¿Cuáles son las oportunidades de crecimiento?"*
3. La respuesta usará enfoque de negocios (ROI, mercado, KPIs)
4. Verás al final: **🎯 Sector: Análisis de Negocios | Tipo: GENERAL**

---

## Paso 5: Crear Tu Sector (2 minutos)

1. Vuelve a **🎨 Diseño de Prompts**
2. Click en tab **➕ Nuevo Sector**
3. Completa:

```
ID: marketing_digital
Nombre: Marketing Digital
Descripción: Estrategias de marketing digital y SEO

System Prompt:
Eres un especialista en marketing digital con expertise en SEO, SEM y analytics.
Proporcionas insights basados en métricas y mejores prácticas.

Directrices:
Enfócate en métricas digitales (CTR, CPC, engagement)
Menciona herramientas específicas
Proporciona recomendaciones medibles
```

4. Click **✨ Crear Sector**
5. Actívalo desde "🎯 Sector Activo"

**¡Listo!** Ahora tienes un RAG personalizado para marketing digital.

---

## Funcionalidades Avanzadas

### Configurar Prompts por Tipo de Consulta

En tab **⚙️ Configurar Sector**:

- **System Prompt**: Comportamiento base
- **Intent Prompts**: Prompts para DEFINITION, COMPARISON, etc.
- **Guidelines**: Reglas que debe seguir

### Probar Antes de Activar

En tab **🧪 Probar Prompts**:

1. Selecciona sector
2. Selecciona tipo de intención
3. Ingresa query de prueba
4. Ve cómo responderá sin ejecutar realmente

### Import/Export

En tab **💾 Import/Export**:

- **Exportar**: Descarga tu configuración completa
- **Importar**: Carga configuración desde archivo JSON

---

## Casos de Uso Rápidos

### Caso 1: Análisis de Contratos

```
1. Activa sector: "Revisión Legal"
2. Sube PDFs de contratos a data/documents/
3. Pregunta: "Identifica cláusulas de riesgo"
→ Respuesta usa terminología legal y señala obligaciones
```

### Caso 2: Documentación Técnica

```
1. Activa sector: "Documentación Técnica"
2. Sube documentación de tu sistema
3. Pregunta: "Explica la arquitectura del sistema"
→ Respuesta técnica con patrones de diseño
```

### Caso 3: Investigación de Mercado

```
1. Crea sector "investigacion_mercado"
2. System prompt: "Eres un analista de mercado..."
3. Guidelines: "Usa datos cuantitativos", "Menciona tendencias"
4. Pregunta: "Analiza el mercado de SaaS"
→ Respuesta con métricas, TAM/SAM, tendencias
```

---

## Troubleshooting Rápido

### No veo cambios después de cambiar sector

✅ **Solución**: Verifica el mensaje "✅ Sector activado" y refresca el navegador

### Error al crear sector

✅ **Solución**: El ID debe ser único, minúsculas, sin espacios (usa `_`)

### Quiero volver a la configuración original

✅ **Solución**:
1. Ve a `config/backups/prompts/`
2. Copia el backup más antiguo
3. Importa desde tab "💾 Import/Export"

---

## Próximos Pasos

1. **Lee la documentación completa**: [PROMPT_DESIGN_SYSTEM.md](./PROMPT_DESIGN_SYSTEM.md)
2. **Ejecuta el demo**: `python demo_prompt_design.py`
3. **Experimenta**: Crea sectores para tus necesidades específicas
4. **Comparte**: Exporta tu configuración y compártela con el equipo

---

## Ayuda

- 📖 [Documentación Completa](./PROMPT_DESIGN_SYSTEM.md)
- 🐛 [Troubleshooting](./PROMPT_DESIGN_SYSTEM.md#troubleshooting)
- 💡 [Mejores Prácticas](./PROMPT_DESIGN_SYSTEM.md#mejores-prácticas)
- 📝 [Casos de Uso](./PROMPT_DESIGN_SYSTEM.md#casos-de-uso)

---

**Tiempo total**: ⏱️ 5 minutos
**Resultado**: 🎉 RAG configurable para cualquier sector

¡Empieza ahora!
