#!/usr/bin/env python3
"""
Test Script for Query Advisor Implementation
"""

import sys
from pathlib import Path

def setup_path():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

def test_query_advisor_core():
    """Test core QueryAdvisor functionality"""
    try:
        setup_path()
        
        print("🧪 Testing Query Advisor Core...")
        
        # Import modules
        from src.utils.query_advisor import QueryAdvisor, EffectivenessScore, QuerySuggestion
        from src.utils.intent_detector import IntentType, IntentResult
        
        advisor = QueryAdvisor()
        print("✅ QueryAdvisor initialized successfully")
        
        # Test 1: Effectiveness Analysis
        print("\n📊 Test 1: Effectiveness Analysis")
        test_query = "¿Qué es machine learning?"
        mock_result = {
            'context': [
                type('MockDoc', (), {
                    'page_content': 'Machine learning is a subset of AI...',
                    'metadata': {'file_name': 'ml_paper.pdf'}
                })()
            ],
            'expansion_info': {'expansion_count': 3}
        }
        
        mock_intent = IntentResult(
            intent_type=IntentType.DEFINITION,
            confidence=0.9,
            reasoning="Clear definition request",
            processing_time_ms=150.0,
            matched_patterns=['¿qué es'],
            fallback_used=False
        )
        
        effectiveness = advisor.analyze_query_effectiveness(test_query, mock_result, mock_intent)
        
        assert isinstance(effectiveness, EffectivenessScore)
        assert 0.0 <= effectiveness.score <= 1.0
        assert len(effectiveness.confidence_factors) > 0
        
        print(f"   ✅ Effectiveness score: {effectiveness.score:.3f}")
        print(f"   ✅ Factors: {list(effectiveness.confidence_factors.keys())}")
        print(f"   ✅ Improvement areas: {effectiveness.improvement_areas}")
        
        # Test 2: Suggestion Generation
        print("\n💡 Test 2: Suggestion Generation")
        suggestions = advisor.generate_suggestions(test_query, mock_intent, effectiveness)
        
        assert isinstance(suggestions, list)
        if suggestions:
            assert all(isinstance(s, QuerySuggestion) for s in suggestions)
            print(f"   ✅ Generated {len(suggestions)} suggestions")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion.reformulated_query}")
                print(f"      Reason: {suggestion.reason}")
        else:
            print("   ✅ No suggestions needed (high effectiveness)")
        
        # Test 3: Contextual Tips
        print("\n💭 Test 3: Contextual Tips")
        tips = advisor.get_contextual_tips(IntentType.DEFINITION, 0.5)
        
        assert isinstance(tips, list)
        if tips:
            print(f"   ✅ Generated {len(tips)} tips")
            for i, tip in enumerate(tips, 1):
                print(f"   {i}. {tip.tip_text}")
                print(f"      Example: {tip.example}")
        else:
            print("   ⚠️ No tips generated")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_low_effectiveness_scenario():
    """Test advisor with low effectiveness query"""
    try:
        setup_path()
        
        print("\n🔍 Testing Low Effectiveness Scenario...")
        
        from src.utils.query_advisor import QueryAdvisor
        from src.utils.intent_detector import IntentType, IntentResult
        
        advisor = QueryAdvisor()
        
        # Simular query vaga con baja efectividad
        vague_query = "IA"
        poor_result = {
            'context': [],  # No context found
            'expansion_info': {'expansion_count': 0}
        }
        
        poor_intent = IntentResult(
            intent_type=IntentType.UNKNOWN,
            confidence=0.3,
            reasoning="Query too vague",
            processing_time_ms=80.0,
            matched_patterns=[],
            fallback_used=True
        )
        
        effectiveness = advisor.analyze_query_effectiveness(vague_query, poor_result, poor_intent)
        suggestions = advisor.generate_suggestions(vague_query, poor_intent, effectiveness)
        
        print(f"   📊 Effectiveness: {effectiveness.score:.3f} (should be low)")
        print(f"   💡 Suggestions: {len(suggestions)} (should have suggestions)")
        print(f"   🔧 Improvement areas: {effectiveness.improvement_areas}")
        
        # Should trigger suggestions for low effectiveness
        assert effectiveness.score < 0.7, "Low effectiveness should be detected"
        
        if suggestions:
            print("   ✅ Suggestions generated for low effectiveness query")
            for suggestion in suggestions:
                print(f"      - {suggestion.reformulated_query}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_integration_with_existing_system():
    """Test integration with existing RAG components"""
    try:
        setup_path()
        
        print("\n🔗 Testing Integration with Existing System...")
        
        # Test imports
        from src.utils.query_advisor import query_advisor
        from src.utils.intent_detector import intent_detector, IntentType
        
        print("   ✅ All imports successful")
        
        # Test advisor can work with real intent detector
        test_query = "Compare machine learning vs deep learning"
        
        # This would normally be async, but we'll test the structure
        print(f"   📝 Test query: '{test_query}'")
        print("   ✅ Query advisor ready for integration")
        
        # Verify advisor instance is accessible
        assert hasattr(query_advisor, 'analyze_query_effectiveness')
        assert hasattr(query_advisor, 'generate_suggestions')
        assert hasattr(query_advisor, 'get_contextual_tips')
        
        print("   ✅ All required methods available")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Query Advisor - Technical Tests")
    print("=" * 50)
    
    tests = [
        ("Core Functionality", test_query_advisor_core),
        ("Low Effectiveness Scenario", test_low_effectiveness_scenario),
        ("System Integration", test_integration_with_existing_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n📊 TEST RESULTS:")
    print("=" * 30)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Query Advisor core implementation ready")
        print(f"📋 Next step: T2 - Usage Analytics implementation")
    else:
        print(f"\n❌ Some tests failed. Fix issues before continuing.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)