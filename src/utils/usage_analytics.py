# -*- coding: utf-8 -*-
"""
Usage Analytics - Pattern Learning and Query Tracking
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from src.utils.intent_detector import IntentType
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class QueryOutcome:
    """Resultado de una consulta para analytics"""
    query: str
    intent_type: str
    effectiveness_score: float
    timestamp: str
    processing_time_ms: float
    suggestion_shown: bool
    suggestion_adopted: bool = False


@dataclass
class QueryPattern:
    """Patrón de consulta exitosa"""
    pattern_template: str
    success_rate: float
    avg_effectiveness: float
    example_queries: List[str]
    intent_type: str
    sample_count: int


class UsageAnalytics:
    """Sistema de analytics para aprendizaje de patrones de consulta"""
    
    def __init__(self, storage_path: str = "data/usage_analytics.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuración
        self.retention_days = 30
        self.min_samples_for_pattern = 3
        
        # Datos en memoria
        self.query_outcomes: List[QueryOutcome] = []
        self.suggestion_adoptions: Dict[str, int] = defaultdict(int)
        self.effectiveness_by_intent: Dict[str, List[float]] = defaultdict(list)
        
        # Cargar datos existentes
        self._load_analytics()
    
    def track_query_outcome(self,
                           query: str,
                           intent_type: IntentType,
                           effectiveness_score: float,
                           processing_time_ms: float = 0.0,
                           suggestion_shown: bool = False) -> None:
        """Registra el resultado de una consulta"""
        try:
            outcome = QueryOutcome(
                query=query.strip(),
                intent_type=intent_type.value if intent_type else "unknown",
                effectiveness_score=effectiveness_score,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=processing_time_ms,
                suggestion_shown=suggestion_shown
            )
            
            # Agregar a memoria
            self.query_outcomes.append(outcome)
            self.effectiveness_by_intent[outcome.intent_type].append(effectiveness_score)
            
            # Limpiar datos antiguos
            self._cleanup_old_data()
            
            # Guardar periódicamente
            if len(self.query_outcomes) % 10 == 0:
                self._save_analytics()
            
            logger.debug(f"Tracked query outcome: {effectiveness_score:.3f} for {intent_type}")
            
        except Exception as e:
            logger.error(f"Error tracking query outcome: {e}")
    
    def track_suggestion_adoption(self, original_query: str, adopted: bool = True) -> None:
        """Registra si el usuario adoptó una sugerencia"""
        try:
            key = "adopted" if adopted else "rejected"
            self.suggestion_adoptions[key] += 1
            
            # Buscar query outcome correspondiente
            for outcome in reversed(self.query_outcomes):
                if outcome.query == original_query and outcome.suggestion_shown:
                    outcome.suggestion_adopted = adopted
                    break
            
            logger.debug(f"Suggestion {key} for query: {original_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error tracking suggestion adoption: {e}")
    
    def get_successful_patterns(self, intent_type: IntentType, min_effectiveness: float = 0.7) -> List[QueryPattern]:
        """Obtiene patrones de consultas exitosas por tipo de intención"""
        try:
            intent_str = intent_type.value if intent_type else "unknown"
            
            # Filtrar consultas exitosas del tipo especificado
            successful_queries = [
                outcome for outcome in self.query_outcomes
                if outcome.intent_type == intent_str and outcome.effectiveness_score >= min_effectiveness
            ]
            
            if len(successful_queries) < self.min_samples_for_pattern:
                return []
            
            # Agrupar por patrones similares
            patterns = self._extract_query_patterns(successful_queries)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting successful patterns: {e}")
            return []
    
    def analyze_failure_modes(self) -> Dict[str, List[Dict]]:
        """Analiza modos de fallo comunes por tipo de intención"""
        try:
            failure_analysis = {}
            
            for intent_type in ["definition", "comparison", "state_of_art", "gap_analysis"]:
                failed_queries = [
                    outcome for outcome in self.query_outcomes
                    if outcome.intent_type == intent_type and outcome.effectiveness_score < 0.5
                ]
                
                if not failed_queries:
                    continue
                
                # Analizar características comunes de fallos
                common_issues = self._analyze_common_issues(failed_queries)
                failure_analysis[intent_type] = common_issues
            
            return failure_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing failure modes: {e}")
            return {}
    
    def get_analytics_summary(self) -> Dict:
        """Obtiene resumen de analytics para dashboard"""
        try:
            total_queries = len(self.query_outcomes)
            if total_queries == 0:
                return {"status": "no_data"}
            
            # Métricas generales
            recent_queries = [
                outcome for outcome in self.query_outcomes
                if self._is_recent(outcome.timestamp, days=7)
            ]
            
            avg_effectiveness = sum(o.effectiveness_score for o in self.query_outcomes) / total_queries
            recent_effectiveness = (
                sum(o.effectiveness_score for o in recent_queries) / len(recent_queries)
                if recent_queries else 0
            )
            
            # Adopción de sugerencias
            total_adoptions = sum(self.suggestion_adoptions.values())
            adoption_rate = (
                self.suggestion_adoptions["adopted"] / total_adoptions
                if total_adoptions > 0 else 0
            )
            
            # Por tipo de intención
            intent_stats = {}
            for intent_type, scores in self.effectiveness_by_intent.items():
                if scores:
                    intent_stats[intent_type] = {
                        "avg_effectiveness": sum(scores) / len(scores),
                        "query_count": len(scores),
                        "success_rate": len([s for s in scores if s >= 0.7]) / len(scores)
                    }
            
            return {
                "total_queries": total_queries,
                "avg_effectiveness": round(avg_effectiveness, 3),
                "recent_effectiveness": round(recent_effectiveness, 3),
                "suggestion_adoption_rate": round(adoption_rate, 3),
                "intent_stats": intent_stats,
                "data_retention_days": self.retention_days,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_improvement_recommendations(self) -> List[Dict]:
        """Genera recomendaciones de mejora basadas en analytics"""
        try:
            recommendations = []
            
            summary = self.get_analytics_summary()
            if summary.get("status") in ["no_data", "error"]:
                return recommendations
            
            # Recomendación por baja efectividad general
            if summary["avg_effectiveness"] < 0.6:
                recommendations.append({
                    "priority": "high",
                    "category": "effectiveness",
                    "message": "La efectividad promedio es baja. Considera mejorar los templates de sugerencias.",
                    "metric": summary["avg_effectiveness"]
                })
            
            # Recomendación por baja adopción de sugerencias
            if summary["suggestion_adoption_rate"] < 0.4:
                recommendations.append({
                    "priority": "medium",
                    "category": "suggestions",
                    "message": "Baja adopción de sugerencias. Revisar relevancia y claridad.",
                    "metric": summary["suggestion_adoption_rate"]
                })
            
            # Recomendaciones por tipo de intención
            intent_stats = summary.get("intent_stats", {})
            for intent_type, stats in intent_stats.items():
                if stats["success_rate"] < 0.5:
                    recommendations.append({
                        "priority": "medium",
                        "category": "intent_specific",
                        "message": f"Baja tasa de éxito para {intent_type}. Revisar template específico.",
                        "metric": stats["success_rate"],
                        "intent_type": intent_type
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _extract_query_patterns(self, successful_queries: List[QueryOutcome]) -> List[QueryPattern]:
        """Extrae patrones de consultas exitosas"""
        patterns = []
        
        # Agrupar por estructura similar
        structure_groups = defaultdict(list)
        
        for outcome in successful_queries:
            # Extraer estructura básica de la consulta
            structure = self._extract_query_structure(outcome.query)
            structure_groups[structure].append(outcome)
        
        # Crear patrones para grupos con suficientes samples
        for structure, outcomes in structure_groups.items():
            if len(outcomes) >= self.min_samples_for_pattern:
                pattern = QueryPattern(
                    pattern_template=structure,
                    success_rate=1.0,  # Solo consultas exitosas
                    avg_effectiveness=sum(o.effectiveness_score for o in outcomes) / len(outcomes),
                    example_queries=[o.query for o in outcomes[:3]],
                    intent_type=outcomes[0].intent_type,
                    sample_count=len(outcomes)
                )
                patterns.append(pattern)
        
        # Ordenar por efectividad promedio
        patterns.sort(key=lambda p: p.avg_effectiveness, reverse=True)
        return patterns[:5]  # Top 5 patterns
    
    def _extract_query_structure(self, query: str) -> str:
        """Extrae estructura generalizada de una consulta"""
        query_lower = query.lower()
        
        # Patrones comunes
        if query_lower.startswith(("¿qué es", "what is")):
            return "definition_pattern"
        elif any(word in query_lower for word in ["compara", "compare", "vs", "versus"]):
            return "comparison_pattern"
        elif any(word in query_lower for word in ["estado del arte", "state of art", "tendencias"]):
            return "state_of_art_pattern"
        elif any(word in query_lower for word in ["limitaciones", "gaps", "oportunidades"]):
            return "gap_analysis_pattern"
        else:
            return "general_pattern"
    
    def _analyze_common_issues(self, failed_queries: List[QueryOutcome]) -> List[Dict]:
        """Analiza issues comunes en consultas fallidas"""
        issues = []
        
        # Analizar longitud de consultas
        query_lengths = [len(o.query.split()) for o in failed_queries]
        avg_length = sum(query_lengths) / len(query_lengths)
        
        if avg_length < 5:
            issues.append({
                "issue": "queries_too_short",
                "description": "Consultas muy cortas (promedio < 5 palabras)",
                "frequency": len([l for l in query_lengths if l < 5]) / len(query_lengths),
                "recommendation": "Sugerir consultas más específicas"
            })
        
        # Analizar falta de términos técnicos
        technical_terms = ["machine learning", "deep learning", "nlp", "ai", "algorithm"]
        queries_without_tech = [
            o for o in failed_queries
            if not any(term in o.query.lower() for term in technical_terms)
        ]
        
        if len(queries_without_tech) / len(failed_queries) > 0.7:
            issues.append({
                "issue": "lack_technical_terms",
                "description": "Falta de terminología técnica específica",
                "frequency": len(queries_without_tech) / len(failed_queries),
                "recommendation": "Promover uso de términos técnicos"
            })
        
        return issues
    
    def _is_recent(self, timestamp_str: str, days: int = 7) -> bool:
        """Verifica si un timestamp es reciente"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            cutoff = datetime.now() - timedelta(days=days)
            return timestamp >= cutoff
        except:
            return False
    
    def _cleanup_old_data(self) -> None:
        """Limpia datos antiguos según política de retención"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        original_count = len(self.query_outcomes)
        self.query_outcomes = [
            outcome for outcome in self.query_outcomes
            if self._is_recent(outcome.timestamp, self.retention_days)
        ]
        
        removed = original_count - len(self.query_outcomes)
        if removed > 0:
            logger.debug(f"Cleaned up {removed} old query outcomes")
    
    def _save_analytics(self) -> None:
        """Guarda analytics en archivo JSON"""
        try:
            data = {
                "query_outcomes": [asdict(outcome) for outcome in self.query_outcomes],
                "suggestion_adoptions": dict(self.suggestion_adoptions),
                "last_saved": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Analytics saved to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Error saving analytics: {e}")
    
    def _load_analytics(self) -> None:
        """Carga analytics desde archivo JSON"""
        try:
            if not self.storage_path.exists():
                logger.debug("No existing analytics file found")
                return
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar query outcomes
            self.query_outcomes = [
                QueryOutcome(**outcome_data)
                for outcome_data in data.get("query_outcomes", [])
            ]
            
            # Cargar suggestion adoptions
            self.suggestion_adoptions = defaultdict(int, data.get("suggestion_adoptions", {}))
            
            # Reconstruir effectiveness_by_intent
            self.effectiveness_by_intent = defaultdict(list)
            for outcome in self.query_outcomes:
                self.effectiveness_by_intent[outcome.intent_type].append(outcome.effectiveness_score)
            
            logger.debug(f"Loaded {len(self.query_outcomes)} query outcomes from analytics")
            
        except Exception as e:
            logger.error(f"Error loading analytics: {e}")
            # Inicializar con datos vacíos en caso de error
            self.query_outcomes = []
            self.suggestion_adoptions = defaultdict(int)
            self.effectiveness_by_intent = defaultdict(list)


# Instancia global
usage_analytics = UsageAnalytics()