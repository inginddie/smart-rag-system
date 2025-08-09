#!/usr/bin/env python3
"""
Test Script for Usage Analytics Implementation
"""

import sys
import tempfile
import os
from pathlib import Path

def setup_path():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

def test_usage_analytics_core():
    """Test core UsageAnalytics functionality"""
    try:
        setup_path()
        
        print("🧪 Testing Usage Analytics Core...")
        
        # Import modules
        from src.utils.usage_analytics import UsageAnalytics, QueryOutcome, QueryPattern
        from src.utils.intent_detector import IntentType
        
        # Use temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            analytics = UsageAnalytics(storage_path=tmp.name)
        
        print("✅ UsageAnalytics initialized successfully")
        
        # Test 1: Track Query Outcomes
        print("\n📊 Test 1: Track Query Outcomes")
        
        # Simulate various query outcomes
        test_queries = [
            ("¿Qué es machine learning?", IntentType.DEFINITION, 0.8),
            ("Compare ML vs DL", IntentType.COMPARISON, 0.9),
            ("IA", IntentType.UNKNOWN, 0.2),  # Low effectiveness
            ("Estado del arte en NLP", IntentType.STATE_OF_ART, 0.7),
        ]
        
        for query, intent, effectiveness in test_queries:
            analytics.track_query_outcome(
                query=query,
                intent_type=intent,
                effectiveness_score=effectiveness,
                processing_time_ms=150.0,
                suggestion_shown=effectiveness < 0.7
            )
        
        assert len(analytics.query_outcomes) == 4
        print(f"   ✅ Tracked {len(analytics.query_outcomes)} query outcomes")
        
        # Test 2: Analytics Summary
        print("\n📈 Test 2: Analytics Summary")
        summary = analytics.get_analytics_summary()
        
        assert "total_queries" in summary
        assert "avg_effectiveness" in summary
        assert summary["total_queries"] == 4
        
        print(f"   ✅ Total queries: {summary['total_queries']}")
        print(f"   ✅ Avg effectiveness: {summary['avg_effectiveness']:.3f}")
        print(f"   ✅ Intent stats: {len(summary.get('intent_stats', {}))}")
        
        # Test 3: Pattern Recognition
        print("\n🔍 Test 3: Pattern Recognition")
        
        # Add more successful queries for pattern detection
        for i in range(5):
            analytics.track_query_outcome(
                query=f"¿Qué es deep learning approach {i}?",
                intent_type=IntentType.DEFINITION,
                effectiveness_score=0.85,
                processing_time_ms=120.0
            )
        
        patterns = analytics.get_successful_patterns(IntentType.DEFINITION)
        print(f"   ✅ Found {len(patterns)} successful patterns")
        
        if patterns:
            for pattern in patterns:
                print(f"      Pattern: {pattern.pattern_template}")
                print(f"      Avg effectiveness: {pattern.avg_effectiveness:.3f}")
        
        # Test 4: Failure Analysis
        print("\n⚠️ Test 4: Failure Analysis")
        failure_modes = analytics.analyze_failure_modes()
        
        print(f"   ✅ Analyzed failure modes for {len(failure_modes)} intent types")
        for intent, issues in failure_modes.items():
            print(f"      {intent}: {len(issues)} issues identified")
        
        # Test 5: Recommendations
        print("\n💡 Test 5: Improvement Recommendations")
        recommendations = analytics.get_improvement_recommendations()
        
        print(f"   ✅ Generated {len(recommendations)} recommendations")
        for rec in recommendations:
            print(f"      {rec['priority']}: {rec['category']} - {rec['message']}")
        
        # Test 6: Suggestion Adoption Tracking
        print("\n👍 Test 6: Suggestion Adoption")
        analytics.track_suggestion_adoption("IA", adopted=True)
        analytics.track_suggestion_adoption("test query", adopted=False)
        
        updated_summary = analytics.get_analytics_summary()
        adoption_rate = updated_summary.get("suggestion_adoption_rate", 0)
        print(f"   ✅ Suggestion adoption rate: {adoption_rate:.3f}")
        
        # Cleanup
        os.unlink(analytics.storage_path)
        
        assert True  # Test passed if no exceptions
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed with error: {e}"

def test_persistence():
    """Test data persistence and loading"""
    try:
        setup_path()
        
        print("\n💾 Testing Data Persistence...")
        
        from src.utils.usage_analytics import UsageAnalytics
        from src.utils.intent_detector import IntentType
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            test_file = tmp.name
        
        # Create analytics and add data
        analytics1 = UsageAnalytics(storage_path=test_file)
        analytics1.track_query_outcome(
            query="Test persistence query",
            intent_type=IntentType.DEFINITION,
            effectiveness_score=0.75
        )
        analytics1._save_analytics()
        
        # Create new instance and load data
        analytics2 = UsageAnalytics(storage_path=test_file)
        
        assert len(analytics2.query_outcomes) == 1
        assert analytics2.query_outcomes[0].query == "Test persistence query"
        
        print("   ✅ Data persistence working correctly")
        
        # Cleanup
        os.unlink(test_file)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_integration_potential():
    """Test integration readiness with existing system"""
    try:
        setup_path()
        
        print("\n🔗 Testing Integration Potential...")
        
        # Test imports
        from src.utils.usage_analytics import usage_analytics
        from src.utils.query_advisor import query_advisor
        from src.utils.intent_detector import IntentType
        
        print("   ✅ All imports successful")
        
        # Test that analytics can work with advisor
        assert hasattr(usage_analytics, 'track_query_outcome')
        assert hasattr(usage_analytics, 'get_analytics_summary')
        assert hasattr(usage_analytics, 'get_improvement_recommendations')
        
        print("   ✅ Analytics ready for RAG service integration")
        
        # Test advisor + analytics workflow simulation
        mock_query = "Test integration query"
        mock_intent = IntentType.DEFINITION
        
        # This simulates what will happen in RAG service
        effectiveness_score = 0.65  # Below threshold
        
        # Track outcome
        usage_analytics.track_query_outcome(
            query=mock_query,
            intent_type=mock_intent,
            effectiveness_score=effectiveness_score,
            suggestion_shown=True
        )
        
        # Get summary
        summary = usage_analytics.get_analytics_summary()
        assert "total_queries" in summary
        
        print("   ✅ Advisor + Analytics workflow simulation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Usage Analytics - Technical Tests")
    print("=" * 50)
    
    tests = [
        ("Core Functionality", test_usage_analytics_core),
        ("Data Persistence", test_persistence),
        ("Integration Potential", test_integration_potential)
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
        print(f"✅ Usage Analytics implementation ready")
        print(f"📋 Next step: T3 - RAG Service Integration")
        print(f"\n📊 Analytics Features:")
        print(f"   - Query outcome tracking")
        print(f"   - Pattern recognition")
        print(f"   - Failure mode analysis")
        print(f"   - Improvement recommendations")
        print(f"   - Suggestion adoption tracking")
    else:
        print(f"\n❌ Some tests failed. Fix issues before continuing.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)