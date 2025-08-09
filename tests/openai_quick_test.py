#!/usr/bin/env python3
"""
Quick OpenAI API Test - Verificación rápida de conectividad
"""

import os
import sys
from pathlib import Path

def quick_openai_test():
    """Test rápido de conectividad con OpenAI"""
    print("🚀 QUICK OPENAI API TEST")
    print("=" * 30)
    
    # Setup path
    project_root = Path(__file__).parent.parent if '__file__' in globals() else Path('.')
    sys.path.insert(0, str(project_root))
    
    # Test 1: Check API key
    print("\n1️⃣ Checking API Key...")
    try:
        from config.settings import settings
        api_key = settings.openai_api_key
        
        if not api_key:
            print("❌ NO API KEY FOUND")
            print("💡 Solution:")
            print("   1. Create .env file in project root")
            print("   2. Add: OPENAI_API_KEY=your_key_here")
            print("   3. Or set environment variable: export OPENAI_API_KEY=your_key")
            return False
        
        if not api_key.startswith('sk-'):
            print("❌ INVALID API KEY FORMAT")
            print(f"   Current: {api_key[:10]}...")
            print("💡 API key should start with 'sk-'")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return False
    
    # Test 2: Test direct OpenAI call
    print("\n2️⃣ Testing Direct OpenAI API...")
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'OpenAI API is working!'"}
            ],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✅ Direct API call successful!")
        print(f"   Response: {result}")
        
    except Exception as e:
        print(f"❌ Direct API call failed: {e}")
        return False
    
    # Test 3: Test LangChain integration
    print("\n3️⃣ Testing LangChain Integration...")
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=api_key
        )
        
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say 'LangChain integration working!'")])
        
        print(f"✅ LangChain integration successful!")
        print(f"   Response: {response.content}")
        
    except ImportError as e:
        print(f"❌ LangChain import failed: {e}")
        print("💡 Try: pip install langchain-openai")
        return False
    except Exception as e:
        print(f"❌ LangChain call failed: {e}")
        return False
    
    # Test 4: Test embeddings
    print("\n4️⃣ Testing Embeddings...")
    try:
        from langchain_openai import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        
        result = embeddings.embed_query("test embedding")
        print(f"✅ Embeddings working!")
        print(f"   Vector dimension: {len(result)}")
        
    except Exception as e:
        print(f"❌ Embeddings failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ OpenAI API integration is working correctly")
    return True

if __name__ == "__main__":
    success = quick_openai_test()
    
    if not success:
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Verify your OpenAI API key is correct")
        print("2. Check your internet connection")
        print("3. Ensure you have credits in your OpenAI account")
        print("4. Try: pip install --upgrade openai langchain-openai")
        sys.exit(1)
    else:
        print("\n✅ Ready to run full RAG system!")
        sys.exit(0)