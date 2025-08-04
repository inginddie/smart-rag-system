# -*- coding: utf-8 -*-
"""
Tests for HU4 Query Preprocessing & Validation System
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.query_validator import QueryValidator, ValidationIssue, ValidationResult
from src.utils.refinement_suggester import RefinementSuggester, RefinementStrategy, RefinementResult


class TestQueryValidator:
    """Test suite for QueryValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = QueryValidator()
    
    def test_detects_vague_queries(self):
        """Test detection of vague queries"""
        # Test single word queries
        result = self.validator.validate_query("IA")
        assert not result.is_valid
        assert ValidationIssue.TOO_VAGUE in result.issues
        
        result = self.validator.validate_query("AI")
        assert not result.is_valid
        assert ValidationIssue.TOO_VAGUE in result.issues
        
        result = self.validator.validate_query("ML")
        assert not result.is_valid
        assert ValidationIssue.TOO_VAGUE in result.issues
    
    def test_accepts_well_formed_queries(self):
        """Test acceptance of well-formed academic queries"""
        well_formed_queries = [
            "¿Qué algoritmos de ML se usan para análisis de requirements?",
            "¿Cómo se aplica deep learning a historias de usuario?",
            "Compara técnicas de NLP para extracción de información de software requirements"
        ]
        
        for query in well_formed_queries:
            result = self.validator.validate_query(query)
            # Should have high confidence even if not perfect
            assert result.confidence > 0.6, f"Query failed: {query}"
    
    def test_detects_out_of_domain_queries(self):
        """Test detection of out-of-domain queries"""
        out_of_domain_queries = [
            "¿Cuál es la mejor receta de paella?",
            "¿Qué tiempo hará mañana?",
            "¿Cuáles son los últimos resultados deportivos?"
        ]
        
        for query in out_of_domain_queries:
            result = self.validator.validate_query(query)
            assert ValidationIssue.OUT_OF_DOMAIN in result.issues, f"Failed to detect out-of-domain: {query}"
    
    def test_detects_general_terms(self):
        """Test detection of too general terms"""
        general_queries = [
            "métodos",
            "técnicas para mejorar",
            "algorithms for optimization"
        ]
        
        for query in general_queries:
            result = self.validator.validate_query(query)
            assert ValidationIssue.TOO_GENERAL in result.issues, f"Failed to detect general terms: {query}"
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # Very vague query should have low confidence
        result = self.validator.validate_query("IA")
        assert result.confidence < 0.7
        
        # Well-formed query should have high confidence
        result = self.validator.validate_query("¿Qué técnicas de machine learning son efectivas para clasificar historias de usuario en proyectos ágiles?")
        assert result.confidence > 0.8
    
    def test_processing_time_sla(self):
        """Test that validation meets SLA requirements"""
        queries = [
            "IA",
            "¿Qué algoritmos de ML se usan para análisis de requirements?",
            "recetas de cocina italiana"
        ]
        
        for query in queries:
            result = self.validator.validate_query(query)
            # Should be under 100ms SLA
            assert result.processing_time_ms < 100, f"SLA violation: {result.processing_time_ms}ms for '{query}'"


class TestRefinementSuggester:
    """Test suite for RefinementSuggester"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.suggester = RefinementSuggester()
        self.validator = QueryValidator()
    
    def test_generates_suggestions_for_vague_queries(self):
        """Test suggestion generation for vague queries"""
        vague_query = "IA"
        validation_result = self.validator.validate_query(vague_query)
        
        refinement_result = self.suggester.generate_refinements(vague_query, validation_result)
        
        assert refinement_result.suggestions_available
        assert len(refinement_result.suggestions) > 0
        assert any(s.strategy == RefinementStrategy.SPECIFICITY for s in refinement_result.suggestions)
    
    def test_generates_context_suggestions(self):
        """Test context addition suggestions"""
        general_query = "métodos para mejorar"
        validation_result = self.validator.validate_query(general_query)
        
        refinement_result = self.suggester.generate_refinements(general_query, validation_result)
        
        assert refinement_result.suggestions_available
        # Should suggest adding context
        context_suggestions = [s for s in refinement_result.suggestions if s.strategy == RefinementStrategy.CONTEXT_ADDITION]
        assert len(context_suggestions) > 0
    
    def test_generates_domain_alignment_suggestions(self):
        """Test domain alignment for out-of-domain queries"""
        out_of_domain_query = "recetas de cocina"
        validation_result = self.validator.validate_query(out_of_domain_query)
        
        refinement_result = self.suggester.generate_refinements(out_of_domain_query, validation_result)
        
        assert refinement_result.suggestions_available
        domain_suggestions = [s for s in refinement_result.suggestions if s.strategy == RefinementStrategy.DOMAIN_ALIGNMENT]
        assert len(domain_suggestions) > 0
    
    def test_suggestion_quality_and_structure(self):
        """Test quality and structure of generated suggestions"""
        vague_query = "ML"
        validation_result = self.validator.validate_query(vague_query)
        
        refinement_result = self.suggester.generate_refinements(vague_query, validation_result)
        
        for suggestion in refinement_result.suggestions:
            # All suggestions should have required fields
            assert suggestion.suggested_query
            assert suggestion.reason
            assert 0.0 <= suggestion.confidence <= 1.0
            assert suggestion.expected_improvement
            assert suggestion.strategy in RefinementStrategy
            assert 1 <= suggestion.priority <= 3
            
            # Suggested query should be longer/more specific
            assert len(suggestion.suggested_query) > len(vague_query)
    
    def test_quick_fixes_generation(self):
        """Test quick fixes generation"""
        vague_query = "IA"
        validation_result = self.validator.validate_query(vague_query)
        
        refinement_result = self.suggester.generate_refinements(vague_query, validation_result)
        
        assert len(refinement_result.quick_fixes) > 0
        # Quick fixes should be helpful strings
        for fix in refinement_result.quick_fixes:
            assert isinstance(fix, str)
            assert len(fix) > 10  # Meaningful fix text
    
    def test_processing_time_sla(self):
        """Test that suggestion generation meets SLA"""
        query = "IA"
        validation_result = self.validator.validate_query(query)
        
        refinement_result = self.suggester.generate_refinements(query, validation_result)
        
        # Should be under 200ms SLA
        assert refinement_result.processing_time_ms < 200
        
    def test_max_suggestions_limit(self):
        """Test that suggestions are limited to max count"""
        query = "IA"
        validation_result = self.validator.validate_query(query)
        
        refinement_result = self.suggester.generate_refinements(query, validation_result)
        
        # Should not exceed 3 suggestions
        assert len(refinement_result.suggestions) <= 3


class TestIntegration:
    """Integration tests for preprocessing components"""
    
    def test_end_to_end_preprocessing_flow(self):
        """Test complete preprocessing flow"""
        validator = QueryValidator()
        suggester = RefinementSuggester()
        
        # Test with vague query
        vague_query = "IA"
        
        # Step 1: Validate
        validation_result = validator.validate_query(vague_query)
        assert not validation_result.is_valid
        assert validation_result.requires_user_input
        
        # Step 2: Generate refinements
        refinement_result = suggester.generate_refinements(vague_query, validation_result)
        assert refinement_result.suggestions_available
        
        # Step 3: Verify suggested queries are better
        for suggestion in refinement_result.suggestions:
            suggested_validation = validator.validate_query(suggestion.suggested_query)
            # Suggested queries should have higher confidence
            assert suggested_validation.confidence > validation_result.confidence
    
    def test_well_formed_query_bypasses_refinement(self):
        """Test that well-formed queries don't require refinement"""
        validator = QueryValidator()
        
        well_formed_query = "¿Qué algoritmos de machine learning son más efectivos para clasificar historias de usuario por prioridad en proyectos ágiles?"
        
        validation_result = validator.validate_query(well_formed_query)
        
        # Should be valid and not require user input
        assert validation_result.is_valid
        assert not validation_result.requires_user_input
        assert validation_result.confidence > 0.7


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])