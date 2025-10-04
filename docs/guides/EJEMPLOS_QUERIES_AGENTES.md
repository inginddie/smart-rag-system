# 🎯 EJEMPLOS DE QUERIES QUE ACTIVAN AGENTES

## 📊 Cómo Funciona la Detección

### DocumentSearchAgent
**Capacidades**: 
1. DOCUMENT_SEARCH → keywords: ["search", "find", "document", "paper"]
2. SYNTHESIS → keywords: ["synthesize", "combine", "integrate"]
3. ACADEMIC_ANALYSIS → keywords: ["academic", "research", "study"]

**Fórmula de Score**:
```
score = matches / total_capabilities
score = matches / 3

Para activar el agente: score > 0.4
Necesitas: 2 o más matches (2/3 = 0.67)
```

## ✅ QUERIES QUE ACTIVAN EL AGENTE (Score > 0.4)

### Nivel Alto (Score: 0.67 - 2 matches)

1. **"Find research papers about deep learning"**
   - ✅ "find" → DOCUMENT_SEARCH
   - ✅ "research" → ACADEMIC_ANALYSIS
   - Score: 2/3 = 0.67

2. **"Search for academic studies on transformers"**
   - ✅ "search" → DOCUMENT_SEARCH
   - ✅ "academic" → ACADEMIC_ANALYSIS
   - Score: 2/3 = 0.67

3. **"Find papers and synthesize the findings"**
   - ✅ "find" → DOCUMENT_SEARCH
   - ✅ "papers" → DOCUMENT_SEARCH (ya contado)
   - ✅ "synthesize" → SYNTHESIS
   - Score: 2/3 = 0.67

4. **"Search documents about research methodologies"**
   - ✅ "search" → DOCUMENT_SEARCH
   - ✅ "documents" → DOCUMENT_SEARCH (ya contado)
   - ✅ "research" → ACADEMIC_ANALYSIS
   - Score: 2/3 = 0.67

5. **"Find academic papers and combine the results"**
   - ✅ "find" → DOCUMENT_SEARCH
   - ✅ "academic" → ACADEMIC_ANALYSIS
   - ✅ "combine" → SYNTHESIS
   - Score: 3/3 = 0.80 (máximo)

### Nivel Medio (Score: 0.33 - 1 match) ❌ NO ACTIVA

6. **"What papers talk about deep learning?"**
   - ✅ "papers" → DOCUMENT_SEARCH
   - Score: 1/3 = 0.33 (muy bajo)

7. **"Show me research on NLP"**
   - ✅ "research" → ACADEMIC_ANALYSIS
   - Score: 1/3 = 0.33 (muy bajo)

## 🎯 QUERIES RECOMENDADAS PARA PROBAR

### En Español (con keywords en inglés)

1. **"Busca papers sobre deep learning y combina los resultados"**
   - ❌ "busca" no es "search"
   - ✅ "papers" → DOCUMENT_SEARCH
   - ✅ "combina" no es "combine"
   - Score: 1/3 = 0.33 ❌

2. **"Find research papers sobre transformers"** (mixto)
   - ✅ "find" → DOCUMENT_SEARCH
   - ✅ "research" → ACADEMIC_ANALYSIS
   - Score: 2/3 = 0.67 ✅

### En Inglés (RECOMENDADO)

1. **"Find research about deep learning architectures"**
   - ✅ "find" → DOCUMENT_SEARCH
   - ✅ "research" → ACADEMIC_ANALYSIS
   - Score: 2/3 = 0.67 ✅

2. **"Search for academic papers on neural networks"**
   - ✅ "search" → DOCUMENT_SEARCH
   - ✅ "academic" → ACADEMIC_ANALYSIS
   - Score: 2/3 = 0.67 ✅

3. **"Find documents about machine learning and synthesize them"**
   - ✅ "find" → DOCUMENT_SEARCH
   - ✅ "documents" → DOCUMENT_SEARCH (ya contado)
   - ✅ "synthesize" → SYNTHESIS
   - Score: 2/3 = 0.67 ✅

4. **"Search papers and combine research findings"**
   - ✅ "search" → DOCUMENT_SEARCH
   - ✅ "papers" → DOCUMENT_SEARCH (ya contado)
   - ✅ "combine" → SYNTHESIS
   - ✅ "research" → ACADEMIC_ANALYSIS
   - Score: 3/3 = 0.80 ✅ (PERFECTO)

## 🔧 SOLUCIÓN: Mejorar Detección

### Opción 1: Bajar el Threshold (Rápido)

En `src/services/rag_service.py`, línea ~220:
```python
# Cambiar de:
if best_agent_info and best_agent_info['score'] > 0.4:

# A:
if best_agent_info and best_agent_info['score'] > 0.3:
```

Esto permitiría queries con 1 solo match (score 0.33).

### Opción 2: Agregar Keywords en Español

En `src/agents/base/agent.py`, método `_get_capability_keywords`:
```python
keyword_map = {
    AgentCapability.DOCUMENT_SEARCH: [
        "search", "find", "document", "paper",
        "busca", "encuentra", "documento", "articulo"  # Español
    ],
    AgentCapability.ACADEMIC_ANALYSIS: [
        "academic", "research", "study",
        "academico", "investigacion", "estudio"  # Español
    ],
    # ...
}
```

### Opción 3: Usar Embeddings (Avanzado)

Reemplazar el matching simple por similitud semántica con embeddings.

## 📝 SCRIPT DE PRUEBA

```python
from src.services.rag_service import RAGService

rag = RAGService()
rag.initialize()

# Queries de prueba
queries = [
    "Find research papers about deep learning",
    "Search for academic studies on transformers",
    "Find documents and synthesize the results",
    "What papers talk about NLP?",  # No debería activar
]

for query in queries:
    result = rag.query(query)
    agent_used = result.get('agent_info', {}).get('agent_used')
    print(f"Query: {query}")
    print(f"Agent: {agent_used or 'RAG Clásico'}")
    print("-" * 50)
```

## 🎯 QUERIES GARANTIZADAS PARA ACTIVAR EL AGENTE

Copia y pega estas en la aplicación:

1. ✅ **"Find research papers about transformers"**
2. ✅ **"Search for academic studies on deep learning"**
3. ✅ **"Find documents about NLP and synthesize them"**
4. ✅ **"Search papers and combine research findings"**
5. ✅ **"Find academic papers on machine learning"**

## ⚠️ IMPORTANTE

**El sistema está funcionando correctamente**, solo que:
- Las keywords son en inglés
- Necesitas 2+ matches para activar el agente
- Queries en español no funcionarán sin agregar keywords en español

**Recomendación**: Usa las queries en inglés de arriba para probar el sistema.

---

**Para activar con queries en español**: Implementa la Opción 2 (agregar keywords en español).
