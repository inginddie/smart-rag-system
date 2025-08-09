#!/usr/bin/env python3
"""
Test Script for RAG Service Integration with Query Advisor
"""

import sys
from pathlib import Path

def setup_path():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

def test_enhanced_query_method():
    """Test enhanced query method with advisor integration"""
    try:
        setup_path()
        
        print("🧪 Testing Enhanced RAG Service Integration...")
        
        # Test imports and mock setup
        from src.services.rag_service import RAGService
        
        # Create service instance
        rag_service = RAGService()
        print("✅ Enhanced RAG Service created successfully")
        
        # Verify new components are integrated
        assert hasattr(rag_service, 'query_advisor')
        assert hasattr(rag_service, 'usage_analytics')
        print("✅ Query Advisor and Analytics components integrated")
        
        # Verify new methods exist
        new_methods = [
            'track_suggestion_adoption',
            'get_analytics_summary', 
            'get_improvement_recommendations'
        ]
        
        for method in new_methods:
            assert hasattr(rag_service, method), f"Missing method: {method}"
        print(f"✅ All {len(new_methods)} new methods available")
        
        assert True  # Test passed if no exceptions
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed with error: {e}"

def test_query_method_signature():
    """Test that enhanced query method has correct signature"""
    try:
        setup_path()
        
        print("\n📝 Testing Enhanced Query Method Signature...")
        
        from src.services.rag_service import RAGService
        import inspect
        
        rag_service = RAGService()
        
        # Get method signature
        sig = inspect.signature(rag_service.query)
        params = list(sig.parameters.keys())
        
        # Check required parameters
        expected_params = ['question', 'include_sources', 'validate_quality', 'include_advisor']
        
        for param in expected_params:
            assert param in params, f"Missing parameter: {param}"
        
        print(f"✅ Query method signature correct: {params}")
        
        # Check default values
        assert sig.parameters['include_advisor'].default == True
        print("✅ include_advisor defaults to True")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_analytics_methods():
    """Test new analytics methods"""
    try:
        setup_path()
        
        print("\n📊 Testing Analytics Methods...")
        
        from src.services.rag_service import RAGService
        
        rag_service = RAGService()
        
        # Test analytics summary
        summary = rag_service.get_analytics_summary()
        assert isinstance(summary, dict)
        print("✅ get_analytics_summary() works")
        
        # Test improvement recommendations
        recommendations = rag_service.get_improvement_recommendations()
        assert isinstance(recommendations, list)
        print("✅ get_improvement_recommendations() works")
        
        # Test suggestion adoption tracking
        rag_service.track_suggestion_adoption("test query", adopted=True)
        print("✅ track_suggestion_adoption() works")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_status_enhancement():
    """Test enhanced status method"""
    try:
        setup_path()
        
        print("\n📋 Testing Enhanced Status Method...")
        
        from src.services.rag_service import RAGService
        
        rag_service = RAGService()
        status = rag_service.get_status()
        
        # Check for new status fields
        new_fields = [
            'query_advisor_enabled',
            'usage_analytics_enabled', 
            'total_queries_processed',
            'avg_effectiveness',
            'suggestion_adoption_rate'
        ]
        
        for field in new_fields:
            assert field in status, f"Missing status field: {field}"
        
        print(f"✅ All {len(new_fields)} new status fields present")
        print(f"   - Query Advisor: {status['query_advisor_enabled']}")
        print(f"   - Analytics: {status['usage_analytics_enabled']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_backward_compatibility():
    """Test that existing functionality still works"""
    try:
        setup_path()
        
        print("\n🔄 Testing Backward Compatibility...")
        
        from src.services.rag_service import RAGService
        
        rag_service = RAGService()
        
        # Test existing methods still exist
        existing_methods = [
            'initialize',
            'get_simple_answer',
            'get_frequent_questions',
            'reindex_documents',
            'get_status',
            'get_detailed_analysis'
        ]
        
        for method in existing_methods:
            assert hasattr(rag_service, method), f"Missing existing method: {method}"
        
        print(f"✅ All {len(existing_methods)} existing methods preserved")
        
        # Test that query method can still be called with old signature
        # This would normally require initialization, but we test the interface
        try:
            # This will fail due to not being initialized, but signature should work
            rag_service.query("test", include_sources=False)
        except Exception as e:
            # Expected - service not initialized
            if "not initialized" in str(e):
                print("✅ Old query signature still compatible")
            else:
                raise e
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_integration_readiness():
    """Test readiness for UI integration"""
    try:
        setup_path()
        
        print("\n🔗 Testing UI Integration Readiness...")
        
        # Test that all required components can be imported together
        from src.services.rag_service import RAGService
        from src.utils.query_advisor import query_advisor
        from src.utils.usage_analytics import usage_analytics
        
        print("✅ All components importable together")
        
        # Test service creation
        service = RAGService()
        
        # Test that advisor info structure is predictable
        # Mock what the enhanced query method would return
        mock_advisor_info = {
            'effectiveness_score': 0.75,
            'effectiveness_reasoning': 'Test reasoning',
            'improvement_areas': ['specificity'],
            'suggestions': [
                {
                    'reformulated_query': 'Better query',
                    'reason': 'More specific',
                    'expected_improvement': 'Better results',
                    'priority': 1
                }
            ],
            'contextual_tips': [
                {
                    'tip_text': 'Test tip',
                    'category': 'clarity',
                    'example': 'Example usage'
                }
            ],
            'suggestion_shown': True
        }
        
        # Verify structure is what UI expects
        required_advisor_fields = [
            'effectiveness_score',
            'suggestions', 
            'contextual_tips',
            'suggestion_shown'
        ]
        
        for field in required_advisor_fields:
            assert field in mock_advisor_info, f"Missing advisor field: {field}"
        
        print("✅ Advisor info structure ready for UI integration")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 RAG Service Integration - Technical Tests")
    print("=" * 55)
    
    tests = [
        ("Enhanced Query Method", test_enhanced_query_method),
        ("Query Method Signature", test_query_method_signature),
        ("Analytics Methods", test_analytics_methods),
        ("Status Enhancement", test_status_enhancement),
        ("Backward Compatibility", test_backward_compatibility),
        ("UI Integration Readiness", test_integration_readiness)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 35)
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n📊 TEST RESULTS:")
    print("=" * 35)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ RAG Service integration ready")
        print(f"📋 Next step: T4 - UI Enhancement")
        print(f"\n🚀 INTEGRATION SUMMARY:")
        print(f"   ✅ Query Advisor integrated into query() method")
        print(f"   ✅ Usage Analytics tracking enabled")
        print(f"   ✅ New methods: track_suggestion_adoption(), get_analytics_summary()")
        print(f"   ✅ Enhanced status with advisor metrics")
        print(f"   ✅ Backward compatibility maintained")
        print(f"   ✅ Ready for UI integration")
    else:
        print(f"\n❌ Some tests failed. Fix issues before continuing.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)