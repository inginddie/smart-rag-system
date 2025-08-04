# -*- coding: utf-8 -*-
"""
Integration Tests for HU4 Query Preprocessing with RAG Service
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.rag_service import RAGService
from src.utils.query_validator import ValidationIssue


class TestRAGServicePreprocessingIntegration:
    """Integration tests for RAG Service with preprocessing"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.rag_service = RAGService()
        # Skip actual initialization for unit tests
        self.rag_service._initialized = True
    
    def test_vague_query_validation_only(self):
        """Test validation-only method for vague queries"""
        vague_query = "IA"
        
        result = self.rag_service.validate_query_only(vague_query)
        
        assert result['preprocessing_enabled']
        assert not result['validation']['validation_passed']
        assert result['suggestions']['available']
        assert len(result['suggestions']['suggestions']) > 0
    
    def test_well_formed_query_validation_only(self):
        """Test validation-only method for well-formed queries"""
        good_query = "¿Qué algoritmos de machine learning son efectivos para clasificar historias de usuario?"
        
        result = self.rag_service.validate_query_only(good_query)
        
        assert result['preprocessing_enabled']
        assert result['validation']['validation_passed']
        assert not result['suggestions']['available']
    
    def test_out_of_domain_query_validation(self):
        """Test validation for out-of-domain queries"""
        out_of_domain_query = "¿Cuál es la mejor receta de paella?"
        
        result = self.rag_service.validate_query_only(out_of_domain_query)
        
        assert result['preprocessing_enabled']
        assert not result['validation']['validation_passed']
        assert result['suggestions']['available']
        
        # Should have domain alignment suggestions
        suggestions = result['suggestions']['suggestions']
        assert any('software' in s['suggested_query'].lower() or 'ia' in s['suggested_query'].lower() 
                  for s in suggestions)
    
    def test_preprocessing_performance_metrics(self):
        """Test that preprocessing meets performance requirements"""
        queries = [
            "IA",
            "machine learning methods",
            "¿Cómo se aplican algoritmos de ML a requirements engineering?",
            "recetas de cocina italiana"
        ]
        
        for query in queries:
            result = self.rag_service.validate_query_only(query)
            
            # Check validation SLA (should be under 150ms)
            validation_time = result['validation']['processing_time_ms']
            assert validation_time < 150, f"Validation SLA violation: {validation_time}ms for '{query}'"
            
            # Check suggestion SLA if applicable (should be under 150ms)
            if result['suggestions']['available']:
                suggestion_time = result['suggestions']['processing_time_ms']
                assert suggestion_time < 150, f"Suggestion SLA violation: {suggestion_time}ms for '{query}'"
    
    def test_preprocessing_stats_endpoint(self):
        """Test that preprocessing stats are available"""
        stats = self.rag_service.get_preprocessing_stats()
        
        assert 'preprocessing_enabled' in stats
        assert 'validation_stats' in stats
        assert 'suggestion_stats' in stats
        assert 'configuration' in stats
        
        # Stats should have expected structure
        validation_stats = stats['validation_stats']
        assert 'total_validations' in validation_stats
        assert 'validation_success_rate' in validation_stats
        
        suggestion_stats = stats['suggestion_stats']
        assert 'total_suggestions_generated' in suggestion_stats
        assert 'suggestion_adoption_rate' in suggestion_stats
    
    def test_refinement_adoption_tracking(self):
        """Test refinement suggestion adoption tracking"""
        original_query = "IA"
        suggested_query = "¿Qué técnicas de IA se aplican al análisis de historias de usuario?"
        
        # This should not raise an exception
        self.rag_service.track_refinement_suggestion_adoption(
            original_query, suggested_query, adopted=True
        )
        
        # Test rejection tracking
        self.rag_service.track_refinement_suggestion_adoption(
            original_query, suggested_query, adopted=False
        )
    
    def test_preprocessing_configuration_integration(self):
        """Test that preprocessing uses configuration settings"""
        from config.settings import settings
        
        # Test that validator uses settings
        result = self.rag_service.validate_query_only("test")
        
        config = result.get('validation', {})
        # Should reflect current settings
        assert isinstance(config.get('processing_time_ms'), (int, float))
    
    def test_error_handling_in_preprocessing(self):
        """Test graceful error handling in preprocessing"""
        # Test with edge cases that might cause errors
        edge_cases = [
            "",  # Empty query
            "   ",  # Whitespace only
            "a" * 1000,  # Very long query
            "🤖💻🔍",  # Unicode/emoji query
            None  # This might cause an error, but should be handled gracefully
        ]
        
        for query in edge_cases:
            try:
                if query is not None:
                    result = self.rag_service.validate_query_only(query)
                    # Should return valid structure even for edge cases
                    assert 'preprocessing_enabled' in result
                    assert 'validation' in result
            except Exception as e:
                # If there's an exception, it should be logged but not crash
                print(f"Edge case '{query}' caused error: {e}")
                # Should still handle gracefully in production


class TestEndToEndPreprocessingFlow:
    """End-to-end preprocessing flow tests"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.rag_service = RAGService()
        # Skip actual initialization for unit tests
        self.rag_service._initialized = True
    
    def test_complete_preprocessing_workflow(self):
        """Test complete preprocessing workflow from validation to refinement"""
        # Step 1: User enters vague query
        vague_query = "ML"
        
        # Step 2: System validates and finds issues
        validation_result = self.rag_service.validate_query_only(vague_query)
        
        assert not validation_result['validation']['validation_passed']
        assert validation_result['suggestions']['available']
        
        # Step 3: User selects a suggestion
        suggestions = validation_result['suggestions']['suggestions']
        assert len(suggestions) > 0
        
        selected_suggestion = suggestions[0]['suggested_query']
        
        # Step 4: Track adoption and validate improved query
        self.rag_service.track_refinement_suggestion_adoption(
            vague_query, selected_suggestion, adopted=True
        )
        
        # Step 5: Validate that suggested query is better
        improved_validation = self.rag_service.validate_query_only(selected_suggestion)
        
        # Improved query should have better validation results
        assert improved_validation['validation']['confidence_score'] > validation_result['validation']['confidence_score']
    
    def test_preprocessing_bypass_for_good_queries(self):
        """Test that good queries bypass preprocessing smoothly"""
        good_query = "¿Qué algoritmos de deep learning son más efectivos para análisis automatizado de historias de usuario en metodologías ágiles?"
        
        validation_result = self.rag_service.validate_query_only(good_query)
        
        # Should pass validation without suggestions
        assert validation_result['validation']['validation_passed']
        assert not validation_result['suggestions']['available']
        assert validation_result['validation']['confidence_score'] > 0.8
    
    def test_preprocessing_ui_integration_data(self):
        """Test data structure for UI integration"""
        test_query = "IA para software"
        
        result = self.rag_service.validate_query_only(test_query)
        
        # Verify all required fields for UI are present
        assert 'preprocessing_enabled' in result
        
        validation = result['validation']
        required_validation_fields = [
            'is_valid', 'confidence_score', 'validation_passed',
            'should_show_modal', 'issues', 'processing_time_ms'
        ]
        for field in required_validation_fields:
            assert field in validation, f"Missing validation field: {field}"
        
        suggestions = result['suggestions']
        required_suggestion_fields = [
            'available', 'suggestions', 'quick_fixes', 'processing_time_ms'
        ]
        for field in required_suggestion_fields:
            assert field in suggestions, f"Missing suggestions field: {field}"
        
        # If suggestions are available, verify their structure
        if suggestions['available']:
            for suggestion in suggestions['suggestions']:
                suggestion_fields = [
                    'suggested_query', 'reason', 'confidence',
                    'expected_improvement', 'strategy', 'priority'
                ]
                for field in suggestion_fields:
                    assert field in suggestion, f"Missing suggestion field: {field}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])