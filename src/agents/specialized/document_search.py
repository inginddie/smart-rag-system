# -*- coding: utf-8 -*-
"""
DocumentSearchAgent - Primer agente especializado del sistema.
Migra y mejora la funcionalidad RAG existente.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from src.agents.base.agent import BaseAgent, AgentResponse, AgentStatus
from src.chains.rag_chain import RAGChain
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import RAGException

logger = setup_logger()

class DocumentSearchAgent(BaseAgent):
    """
    Agente especializado en búsqueda y análisis de documentos.
    
    Capacidades:
    - Búsqueda semántica en documentos
    - Extracción de información específica  
    - Análisis de contenido académico
    - Filtrado por metadatos
    """
    
    def __init__(self, 
                 vector_store_manager: VectorStoreManager = None,
                 rag_chain: RAGChain = None,
                 memory_manager = None):
        
        super().__init__(
            name="DocumentSearchAgent",
            description="Especialista en búsqueda y análisis de documentos académicos",
            memory_manager=memory_manager
        )
        
        self.vector_store_manager = vector_store_manager or VectorStoreManager()
        self.rag_chain = rag_chain or RAGChain()
        
        # Especializaciones de búsqueda
        self.search_strategies = {
            "semantic": self._semantic_search,
            "keyword": self._keyword_search, 
            "metadata": self._metadata_search,
            "academic": self._academic_search
        }
        
        logger.info(f"DocumentSearchAgent initialized with {len(self.search_strategies)} search strategies")
    
    def get_capabilities(self) -> List[str]:
        """Capacidades específicas del agente"""
        return [
            "document search",
            "semantic search", 
            "academic analysis",
            "paper lookup",
            "literature review",
            "methodology extraction",
            "citation analysis",
            "content summarization",
            "keyword search",
            "metadata filtering"
        ]
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Procesa consultas de búsqueda de documentos
        """
        self.update_status(AgentStatus.THINKING)
        start_time = time.time()
        
        try:
            # Analizar tipo de consulta
            search_strategy = self._determine_search_strategy(query, context)
            
            logger.info(f"DocumentSearchAgent processing query with strategy: {search_strategy}")
            
            self.update_status(AgentStatus.ACTING)
            
            # Ejecutar búsqueda específica
            if search_strategy in self.search_strategies:
                result = await self.search_strategies[search_strategy](query, context)
            else:
                # Fallback a búsqueda RAG clásica
                result = await self._rag_search(query, context)
            
            # Evaluar calidad de resultados
            confidence = self._evaluate_result_quality(result, query)
            
            # Extraer fuentes para transparencia
            sources = self._extract_sources(result)
            
            response = AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                content=result.get("answer", "No se encontró información relevante."),
                confidence=confidence,
                metadata={
                    "search_strategy": search_strategy,
                    "processing_time": time.time() - start_time,
                    "sources_count": len(sources),
                    "model_info": result.get("model_info", {})
                },
                sources=sources,
                reasoning=f"Utilicé estrategia '{search_strategy}' para buscar en {len(sources)} documentos"
            )
            
            # Guardar en memoria para aprendizaje futuro
            self.remember(
                key=f"query_{hash(query)}",
                value={
                    "query": query,
                    "strategy": search_strategy,
                    "confidence": confidence,
                    "sources_count": len(sources)
                },
                context="search_history"
            )
            
            self.update_status(AgentStatus.COMPLETED)
            self.performance_metrics["queries_processed"] += 1
            
            return response
            
        except Exception as e:
            self.update_status(AgentStatus.ERROR)
            self.performance_metrics["errors"] += 1
            logger.error(f"DocumentSearchAgent error: {e}")
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                content=f"Error en la búsqueda: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
                reasoning="Error durante el procesamiento de la consulta"
            )
    
    def _determine_search_strategy(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Determina la mejor estrategia de búsqueda para la consulta
        """
        query_lower = query.lower()
        
        # Estrategia académica para términos específicos
        academic_keywords = [
            "metodología", "methodology", "framework", "approach",
            "estado del arte", "state of art", "literatura", "literature",
            "paper", "artículo", "estudio", "study", "análisis", "analysis"
        ]
        
        if any(keyword in query_lower for keyword in academic_keywords):
            return "academic"
        
        # Estrategia por metadatos
        metadata_keywords = ["autor", "author", "año", "year", "journal", "conference"]
        if any(keyword in query_lower for keyword in metadata_keywords):
            return "metadata"
        
        # Estrategia por palabras clave específicas
        if any(char in query for char in ['"', "'", "exacto", "exact"]):
            return "keyword"
        
        # Por defecto, búsqueda semántica
        return "semantic"
    
    async def _semantic_search(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Búsqueda semántica usando embeddings"""
        try:
            # Usar RAG chain existente con mejoras
            result = self.rag_chain.invoke(query)
            
            # Enriquecer con análisis semántico adicional
            if context and context.get("academic_focus"):
                result = await self._enhance_academic_context(result, query)
            
            return result
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return {"answer": f"Error en búsqueda semántica: {e}", "context": []}
    
    async def _keyword_search(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Búsqueda por palabras clave exactas"""
        try:
            # Extraer palabras clave de la consulta
            keywords = self._extract_keywords(query)
            
            # Búsqueda directa en vector store con filtros
            documents = []
            for keyword in keywords:
                docs = self.vector_store_manager.similarity_search(
                    keyword, 
                    k=3
                )
                documents.extend(docs)
            
            # Eliminar duplicados
            seen_sources = set()
            unique_docs = []
            for doc in documents:
                source_id = doc.metadata.get('source_file', '')
                if source_id not in seen_sources:
                    unique_docs.append(doc)
                    seen_sources.add(source_id)
            
            # Generar respuesta basada en documentos encontrados
            if unique_docs:
                context_text = "\n\n".join([doc.page_content[:500] for doc in unique_docs[:5]])
                answer = f"Encontré información sobre '{query}' en {len(unique_docs)} documentos:\n\n{context_text[:1000]}..."
            else:
                answer = f"No encontré coincidencias exactas para: {', '.join(keywords)}"
            
            return {
                "answer": answer,
                "context": unique_docs,
                "search_type": "keyword",
                "keywords_used": keywords
            }
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return {"answer": f"Error en búsqueda por palabras clave: {e}", "context": []}
    
    async def _metadata_search(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Búsqueda basada en metadatos"""
        try:
            # Extraer criterios de metadatos de la consulta
            metadata_filters = self._parse_metadata_query(query)
            
            # Realizar búsqueda con filtros
            all_docs = self.vector_store_manager.similarity_search(query, k=20)
            
            # Filtrar por metadatos manualmente
            filtered_docs = []
            for doc in all_docs:
                if self._matches_metadata_filter(doc, metadata_filters):
                    filtered_docs.append(doc)
            
            if filtered_docs:
                # Generar respuesta basada en metadatos
                answer = self._generate_metadata_response(filtered_docs, metadata_filters)
            else:
                answer = f"No encontré documentos que coincidan con los criterios: {metadata_filters}"
            
            return {
                "answer": answer,
                "context": filtered_docs,
                "search_type": "metadata",
                "filters_applied": metadata_filters
            }
            
        except Exception as e:
            logger.error(f"Metadata search error: {e}")
            return {"answer": f"Error en búsqueda por metadatos: {e}", "context": []}
    
    async def _academic_search(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Búsqueda especializada para consultas académicas"""
        try:
            # Usar RAG con prompt académico especializado
            academic_query = self._enhance_academic_query(query)
            result = self.rag_chain.invoke(academic_query)
            
            # Post-procesar para formato académico
            if result.get("context"):
                result = await self._enhance_academic_response(result, query)
            
            return result
            
        except Exception as e:
            logger.error(f"Academic search error: {e}")
            return {"answer": f"Error en búsqueda académica: {e}", "context": []}
    
    async def _rag_search(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Búsqueda RAG clásica como fallback"""
        try:
            return self.rag_chain.invoke(query)
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return {"answer": f"Error en búsqueda RAG: {e}", "context": []}
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrae palabras clave de una consulta"""
        import re
        
        # Eliminar palabras comunes
        stop_words = {
            "el", "la", "de", "que", "y", "a", "en", "un", "es", "se", "no", "te", 
            "lo", "le", "da", "su", "por", "son", "con", "para", "como", "las", 
            "del", "una", "al", "todo", "esta", "sus", "me", "yo", "muy", "sin",
            "sobre", "entre", "ser", "tiene", "también", "hasta", "hay", "donde",
            "han", "quien", "están", "puede", "qué", "está"
        }
        
        # Extraer palabras
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Buscar frases entre comillas
        quoted_phrases = re.findall(r'"([^"]*)"', query)
        keywords.extend(quoted_phrases)
        
        return keywords[:10]  # Limitar a 10 palabras clave
    
    def _parse_metadata_query(self, query: str) -> Dict[str, str]:
        """Extrae filtros de metadatos de la consulta"""
        filters = {}
        query_lower = query.lower()
        
        import re
        
        # Año
        year_match = re.search(r'(\d{4})', query)
        if year_match:
            filters['year'] = year_match.group(1)
        
        # Autor (patrón básico)
        author_patterns = [
            r'autor[:\s]+([a-zA-Z\s]+)',
            r'author[:\s]+([a-zA-Z\s]+)',
            r'de\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                filters['author'] = match.group(1).strip()
                break
        
        return filters
    
    def _matches_metadata_filter(self, doc, filters: Dict[str, str]) -> bool:
        """Verifica si un documento coincide con los filtros de metadatos"""
        metadata = doc.metadata
        
        for key, value in filters.items():
            if key == 'year':
                # Buscar año en metadatos o contenido
                doc_year = metadata.get('year') or metadata.get('publication_year')
                if not doc_year:
                    # Buscar en el nombre del archivo o contenido
                    source_file = metadata.get('source_file', '')
                    if value not in source_file and value not in doc.page_content[:200]:
                        return False
                elif str(doc_year) != value:
                    return False
            
            elif key == 'author':
                # Buscar autor en metadatos o contenido
                doc_author = metadata.get('author', '')
                source_file = metadata.get('source_file', '')
                content_preview = doc.page_content[:300].lower()
                
                if (value.lower() not in doc_author.lower() and 
                    value.lower() not in source_file.lower() and
                    value.lower() not in content_preview):
                    return False
        
        return True
    
    def _generate_metadata_response(self, docs, filters: Dict[str, str]) -> str:
        """Genera respuesta basada en documentos filtrados por metadatos"""
        response_parts = []
        
        response_parts.append(f"Encontré {len(docs)} documentos que coinciden con los criterios:")
        
        for key, value in filters.items():
            response_parts.append(f"- {key}: {value}")
        
        response_parts.append("\nDocumentos encontrados:")
        
        for i, doc in enumerate(docs[:5], 1):
            source = doc.metadata.get('source_file', 'Fuente desconocida')
            preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
            response_parts.append(f"\n{i}. {source}\n   {preview}")
        
        if len(docs) > 5:
            response_parts.append(f"\n... y {len(docs) - 5} documentos adicionales.")
        
        return "\n".join(response_parts)
    
    def _enhance_academic_query(self, query: str) -> str:
        """Mejora una consulta para búsqueda académica"""
        academic_prefixes = [
            "Desde una perspectiva académica,",
            "Basándote en la literatura científica,", 
            "Según los estudios de investigación,"
        ]
        
        # Seleccionar prefijo apropiado
        if "metodología" in query.lower() or "method" in query.lower():
            prefix = academic_prefixes[0]
        elif "literatura" in query.lower() or "literature" in query.lower():
            prefix = academic_prefixes[1]
        else:
            prefix = academic_prefixes[2]
        
        return f"{prefix} {query}. Incluye referencias específicas a papers y autores cuando sea posible."
    
    async def _enhance_academic_context(self, result: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Enriquece respuesta con contexto académico adicional"""
        context_docs = result.get("context", [])
        
        if context_docs:
            # Extraer información académica adicional
            academic_info = self._extract_academic_info(context_docs)
            
            # Enriquecer la respuesta
            original_answer = result.get("answer", "")
            enhanced_answer = f"{original_answer}\n\n**Contexto Académico:**\n{academic_info}"
            
            result["answer"] = enhanced_answer
            result["academic_enhancement"] = academic_info
        
        return result
    
    async def _enhance_academic_response(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Post-procesa respuesta para formato académico"""
        answer = result.get("answer", "")
        context_docs = result.get("context", [])
        
        if context_docs:
            # Agregar sección de referencias
            references = self._generate_references_section(context_docs)
            enhanced_answer = f"{answer}\n\n**Referencias Consultadas:**\n{references}"
            
            result["answer"] = enhanced_answer
            result["references"] = references
        
        return result
    
    def _extract_academic_info(self, docs) -> str:
        """Extrae información académica relevante de los documentos"""
        info_parts = []
        
        # Contar documentos únicos
        unique_sources = set()
        for doc in docs:
            source = doc.metadata.get('source_file', '')
            if source:
                unique_sources.add(source)
        
        info_parts.append(f"- Fuentes consultadas: {len(unique_sources)} documentos")
        
        # Buscar menciones de metodologías
        methodologies = set()
        for doc in docs:
            content = doc.page_content.lower()
            method_keywords = ["methodology", "metodología", "framework", "approach", "method", "technique"]
            for keyword in method_keywords:
                if keyword in content:
                    # Extraer contexto alrededor de la palabra
                    import re
                    matches = re.finditer(rf'\b{keyword}\b', content)
                    for match in matches:
                        start = max(0, match.start() - 30)
                        end = min(len(content), match.end() + 30)
                        context = content[start:end].strip()
                        if len(context) > 10:
                            methodologies.add(context)
                            break
        
        if methodologies:
            info_parts.append(f"- Metodologías identificadas: {len(methodologies)}")
        
        return "\n".join(info_parts)
    
    def _generate_references_section(self, docs) -> str:
        """Genera sección de referencias a partir de documentos"""
        references = []
        seen_sources = set()
        
        for doc in docs:
            source_file = doc.metadata.get('source_file', '')
            if source_file and source_file not in seen_sources:
                # Extraer nombre limpio del archivo
                file_name = source_file.split('/')[-1].replace('.pdf', '').replace('_', ' ')
                references.append(f"- {file_name}")
                seen_sources.add(source_file)
        
        return "\n".join(references[:10])  # Limitar a 10 referencias
    
    def _evaluate_result_quality(self, result: Dict[str, Any], query: str) -> float:
        """Evalúa la calidad del resultado obtenido"""
        confidence = 0.5  # Base confidence
        
        # Factores que aumentan confianza
        context_docs = result.get("context", [])
        answer = result.get("answer", "")
        
        # Número de fuentes
        if len(context_docs) >= 3:
            confidence += 0.2
        elif len(context_docs) >= 1:
            confidence += 0.1
        
        # Longitud de respuesta (respuestas muy cortas o largas pueden ser problemáticas)
        if 50 <= len(answer) <= 2000:
            confidence += 0.1
        
        # Presencia de información específica
        if any(keyword in answer.lower() for keyword in ["según", "basado", "evidencia", "estudio"]):
            confidence += 0.1
        
        # Penalizar respuestas de error
        if "error" in answer.lower() or "no se encontró" in answer.lower():
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _extract_sources(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae información de fuentes del resultado"""
        sources = []
        context_docs = result.get("context", [])
        query = result.get("query", "")
        
        for i, doc in enumerate(context_docs):
            # Calcular relevancia basada en múltiples factores
            relevance_score = self._calculate_relevance_score(doc, query, position=i)

            source_info = {
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "page_number": doc.metadata.get("page_number"),
                "section_title": doc.metadata.get("section_title"),
                "doc_type": doc.metadata.get("doc_type"),
                "metadata": doc.metadata,
                "relevance": self._score_to_category(relevance_score),
                "relevance_score": round(relevance_score, 3)
            }
            sources.append(source_info)
        
        return sources
    
    def _calculate_relevance_score(self, doc, query: str, position: int) -> float:
        """Calcula score de relevancia basado en múltiples factores"""
        content = doc.page_content.lower()
        query_lower = query.lower()
        
        # Factor 1: Similitud por palabras clave (0.0-0.4)
        query_words = set(query_lower.split())
        content_words = set(content.split())
        
        if query_words:
            keyword_overlap = len(query_words.intersection(content_words)) / len(query_words)
            keyword_score = min(0.4, keyword_overlap * 0.4)
        else:
            keyword_score = 0.0
        
        # Factor 2: Posición en resultados (0.0-0.3)
        # Los primeros resultados son más relevantes
        position_score = max(0.0, 0.3 * (1 - position / 10))
        
        # Factor 3: Longitud del contenido (0.0-0.2) 
        # Contenido ni muy corto ni muy largo es mejor
        content_length = len(doc.page_content)
        if 50 <= content_length <= 1000:
            length_score = 0.2
        elif content_length < 50:
            length_score = 0.05
        else:
            length_score = max(0.1, 0.2 * (1000 / content_length))
        
        # Factor 4: Presencia de términos académicos (0.0-0.1)
        academic_terms = ["según", "basado en", "evidencia", "estudio", "investigación", "análisis"]
        academic_score = 0.0
        for term in academic_terms:
            if term in content:
                academic_score += 0.02
        academic_score = min(0.1, academic_score)
        
        # Score total (0.0-1.0)
        total_score = keyword_score + position_score + length_score + academic_score
        return min(1.0, total_score)
    
    def _score_to_category(self, score: float) -> str:
        """Convierte score numérico a categoría"""
        if score >= 0.8:
            return "very_high"
        elif score >= 0.6:
            return "high" 
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "very_low"

    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Evalúa si el agente puede manejar una consulta específica
        """
        base_score = super().can_handle_query(query, context)
        
        # Bonus por términos académicos específicos
        academic_terms = [
            "documento", "paper", "artículo", "estudio", "investigación",
            "literatura", "metodología", "análisis", "revisión", "buscar",
            "encontrar", "localizar", "extraer"
        ]
        
        query_lower = query.lower()
        academic_matches = sum(1 for term in academic_terms if term in query_lower)
        
        # Calcular score final
        academic_bonus = min(0.3, academic_matches * 0.1)
        final_score = min(1.0, base_score + academic_bonus)
        
        return final_score

# Función de utilidad para crear agente con dependencias
def create_document_search_agent(vector_store_manager=None, rag_chain=None, memory_manager=None):
    """Factory function para crear DocumentSearchAgent"""
    return DocumentSearchAgent(
        vector_store_manager=vector_store_manager,
        rag_chain=rag_chain, 
        memory_manager=memory_manager
    )