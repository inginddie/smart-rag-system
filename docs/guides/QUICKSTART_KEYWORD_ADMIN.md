# 🚀 Quick Start: Administración de Keywords

## ⚡ Inicio Rápido (5 minutos)

### 1. Iniciar la Aplicación

```bash
python ui/gradio_app.py
```

### 2. Inicializar el Sistema

1. Abre tu navegador en `http://localhost:7860`
2. Ve al tab **"⚙️ Administración"**
3. Presiona **"🚀 Inicializar Sistema"**
4. Espera el mensaje: ✅ Sistema RAG inicializado correctamente

### 3. Acceder al Panel de Keywords

1. Ve al tab **"🔧 Administración"** (nuevo tab que aparece)
2. Verás las estadísticas del sistema

---

## 📊 Entender las Estadísticas

```
Agentes Totales: 1          # Número de agentes configurados
Agentes Activos: 1          # Agentes habilitados
Capacidades Totales: 3      # Capacidades disponibles
Keywords Totales: 20        # Total de keywords configuradas
Última Actualización: ...   # Timestamp del último cambio
Configuración Válida: Sí    # Estado de validación
```

---

## 🧪 Probar Activación de Agentes

### Ejemplo 1: Query en Inglés

```
Query: Find research papers about deep learning

Resultado:
✅ DocumentSearchAgent SE ACTIVARÍA
   Score: 0.67 / 0.30
   Keywords detectadas:
   - DOCUMENT_SEARCH: search, find, paper
   - ACADEMIC_ANALYSIS: research
```

### Ejemplo 2: Query en Español

```
Query: Buscar documentos sobre inteligencia artificial

Resultado:
✅ DocumentSearchAgent SE ACTIVARÍA
   Score: 0.33 / 0.30
   Keywords detectadas:
   - DOCUMENT_SEARCH: document, buscar, documento
```

### Ejemplo 3: Query que NO activa

```
Query: What is machine learning?

Resultado:
❌ DocumentSearchAgent NO SE ACTIVARÍA
   Score: 0.00 / 0.30
```

---

## ➕ Agregar Keywords

### Paso a Paso:

1. **Expandir la capacidad** (ej: "📄 DOCUMENT_SEARCH")
2. **Ver keywords actuales** en el textbox
3. **Escribir nueva keyword** en "Nueva Keyword"
   - Ejemplo: `investigar`
4. **Presionar "➕ Agregar"**
5. **Ver confirmación**: ✅ Keyword 'investigar' agregada exitosamente
6. **Verificar** que aparece en la lista

### Probar la Nueva Keyword:

```
Query: Quiero investigar sobre machine learning

Resultado:
✅ DocumentSearchAgent SE ACTIVARÍA
   Keywords detectadas:
   - DOCUMENT_SEARCH: investigar ← ¡Nueva keyword detectada!
```

---

## 🗑️ Eliminar Keywords

### Paso a Paso:

1. **Expandir la capacidad**
2. **Ver keywords actuales** para saber cuál eliminar
3. **Escribir keyword exacta** en "Keyword a Eliminar"
   - Ejemplo: `investigar`
4. **Presionar "🗑️ Eliminar"**
5. **Ver confirmación**: ✅ Keyword 'investigar' eliminada exitosamente

---

## ⚙️ Ajustar Threshold

### ¿Qué es el Threshold?

El threshold es el **score mínimo** para que un agente se active.

- **Threshold bajo (0.1-0.3)**: Agente se activa fácilmente
- **Threshold medio (0.4-0.6)**: Balance entre precisión y cobertura
- **Threshold alto (0.7-1.0)**: Solo queries muy específicas

### Cómo Ajustar:

1. **Mover el slider** "Threshold de Activación"
2. **Presionar "💾 Actualizar Threshold"**
3. **Ver confirmación**: ✅ Threshold actualizado a 0.50

### Ejemplo de Impacto:

```
Query: Find papers
Threshold 0.3: ✅ SE ACTIVARÍA (score: 0.33)
Threshold 0.5: ❌ NO SE ACTIVARÍA (score: 0.33)
```

---

## 🔄 Acciones del Sistema

### Recargar Configuración

- **Cuándo usar**: Después de cambios manuales en archivos
- **Cómo**: Presionar "🔄 Recargar Configuración"
- **Resultado**: Recarga desde `config/agent_keywords.json`

### Resetear a Defaults

- **Cuándo usar**: Para volver a configuración original
- **Cómo**: Presionar "⚠️ Resetear a Defaults"
- **Resultado**: Restaura keywords originales del sistema
- **⚠️ Advertencia**: Perderás cambios personalizados

### Exportar Configuración

- **Cuándo usar**: Para backup o migración
- **Cómo**: Presionar "📤 Exportar Config"
- **Resultado**: Descarga archivo JSON con configuración actual

---

## 📁 Archivos Importantes

### Configuración Principal

```
config/agent_keywords.json
```

Este archivo contiene toda la configuración de keywords.

### Backups Automáticos

```
config/backups/agent_keywords_YYYYMMDD_HHMMSS.json
```

Se crean automáticamente antes de cada cambio. Se mantienen los últimos 10.

---

## 🎯 Casos de Uso Comunes

### Caso 1: Agregar Soporte para Nuevo Idioma

**Objetivo**: Agregar keywords en portugués

```
1. Expandir "DOCUMENT_SEARCH"
2. Agregar: "pesquisar"
3. Agregar: "procurar"
4. Agregar: "documento"
5. Probar: "Pesquisar documentos sobre IA"
```

### Caso 2: Hacer el Agente Más Selectivo

**Objetivo**: Reducir falsos positivos

```
1. Ajustar threshold de 0.3 a 0.5
2. Probar queries ambiguas
3. Verificar que solo queries claras activan el agente
```

### Caso 3: Agregar Términos Específicos del Dominio

**Objetivo**: Mejorar detección en tu área de investigación

```
1. Expandir "ACADEMIC_ANALYSIS"
2. Agregar: "metodologia"
3. Agregar: "framework"
4. Agregar: "hipotesis"
5. Probar con queries de tu dominio
```

---

## 🐛 Troubleshooting

### Problema: El tab "🔧 Administración" no aparece

**Solución**:
1. Ve a "⚙️ Administración"
2. Presiona "🚀 Inicializar Sistema"
3. Recarga la página del navegador

### Problema: Los cambios no se aplican

**Solución**:
1. Presiona "🔄 Recargar Configuración"
2. Verifica que veas el mensaje de confirmación
3. Prueba nuevamente con una query

### Problema: Error al agregar keyword

**Solución**:
1. Verifica que la keyword no esté vacía
2. Verifica que no contenga caracteres especiales
3. Intenta con una palabra simple primero

### Problema: Quiero volver atrás

**Solución**:
1. Los backups están en `config/backups/`
2. Copia el backup deseado a `config/agent_keywords.json`
3. Presiona "🔄 Recargar Configuración"

O simplemente:
1. Presiona "⚠️ Resetear a Defaults"

---

## 💡 Tips y Mejores Prácticas

### ✅ DO:
- Prueba cada keyword después de agregarla
- Usa palabras simples y claras
- Mantén keywords en minúsculas
- Agrega sinónimos en diferentes idiomas
- Ajusta threshold basado en resultados reales

### ❌ DON'T:
- No uses frases completas como keywords
- No uses caracteres especiales
- No pongas threshold muy alto (>0.8)
- No elimines todas las keywords de una capacidad
- No olvides probar después de cambios

---

## 📚 Recursos Adicionales

- **Documentación Completa**: `HU2_KEYWORD_ADMIN_COMPLETADO.md`
- **Resumen Técnico**: `IMPLEMENTACION_KEYWORD_ADMIN_RESUMEN.md`
- **Script de Pruebas**: `test_keyword_admin.py`

---

## 🎉 ¡Listo!

Ahora puedes gestionar keywords dinámicamente y mejorar la activación de agentes en tu sistema RAG.

**¿Preguntas?** Revisa la documentación completa o ejecuta el script de pruebas.

---

**Versión**: 1.0.0  
**Última Actualización**: 2025-10-03
