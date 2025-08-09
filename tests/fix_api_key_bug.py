#!/usr/bin/env python3
"""
BUG #1 FIX: API Key Validation and Correction
Solución completa para el problema de API key inválida
"""

import os
import sys
from pathlib import Path

def fix_api_key_bug():
    """Diagnóstica y corrige el problema de API key"""
    print("🔧 FIXING BUG #1: API KEY INVALID")
    print("=" * 40)
    
    # Setup path
    project_root = Path(__file__).parent.parent if '__file__' in globals() else Path('.')
    sys.path.insert(0, str(project_root))
    
    # Step 1: Diagnóstico actual
    print("\n1️⃣ Current API Key Diagnosis...")
    
    try:
        from config.settings import settings
        current_key = settings.openai_api_key
        
        if current_key:
            print(f"   📋 Current key: {current_key[:15]}...{current_key[-8:]}")
            print(f"   📏 Length: {len(current_key)} characters")
            
            # Validar formato
            if current_key.startswith('sk-proj-'):
                print("   ✅ Format: Project API key (correct)")
            elif current_key.startswith('sk-'):
                print("   ⚠️ Format: Legacy API key (may work)")
            else:
                print("   ❌ Format: Invalid format")
                
        else:
            print("   ❌ No API key found")
            
    except Exception as e:
        print(f"   ❌ Error loading settings: {e}")
        return False
    
    # Step 2: Test current key
    print("\n2️⃣ Testing Current API Key...")
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=current_key)
        
        # Test with minimal request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        
        print("   ✅ API Key is VALID and working!")
        print(f"   📝 Test response: {response.choices[0].message.content}")
        return True
        
    except openai.AuthenticationError as e:
        print("   ❌ AUTHENTICATION ERROR: Invalid API key")
        print(f"   🔍 Details: {str(e)}")
        
    except openai.RateLimitError as e:
        print("   ⚠️ RATE LIMIT: API key is valid but rate limited")
        print(f"   💡 This means the key works, just try again later")
        return True
        
    except openai.InsufficientQuotaError as e:
        print("   ⚠️ QUOTA EXCEEDED: API key valid but no credits")
        print("   💳 Please add credits to your OpenAI account")
        print("   🔗 Visit: https://platform.openai.com/account/billing")
        return True
        
    except Exception as e:
        print(f"   ❌ Other error: {e}")
    
    # Step 3: Guía de corrección
    print("\n3️⃣ API Key Correction Guide...")
    
    print("\n📋 STEPS TO FIX YOUR API KEY:")
    print("=" * 35)
    
    print("\n🔑 Option A: Get New API Key from OpenAI")
    print("   1. Visit: https://platform.openai.com/account/api-keys")
    print("   2. Click 'Create new secret key'")
    print("   3. Copy the new key (starts with sk-)")
    print("   4. Replace in your .env file")
    
    print("\n💳 Option B: Check Account Status")
    print("   1. Visit: https://platform.openai.com/account/billing")
    print("   2. Verify you have available credits")
    print("   3. Add payment method if needed")
    
    print("\n⚙️ Option C: Update Environment")
    print("   1. Open .env file in project root")
    print("   2. Update: OPENAI_API_KEY=your_new_key_here")
    print("   3. Restart the application")
    
    # Step 4: Interactive fix
    print("\n4️⃣ Interactive API Key Update...")
    
    update_choice = input("\n❓ Do you want to update the API key now? (y/N): ").lower()
    
    if update_choice in ['y', 'yes']:
        new_key = input("\n🔑 Enter your new OpenAI API key: ").strip()
        
        if new_key:
            if validate_api_key_format(new_key):
                # Update .env file
                env_file = project_root / '.env'
                
                if update_env_file(env_file, new_key):
                    print("   ✅ API key updated successfully!")
                    
                    # Test new key
                    print("\n🧪 Testing new API key...")
                    if test_api_key(new_key):
                        print("   🎉 New API key is working!")
                        return True
                    else:
                        print("   ❌ New API key is still not working")
                        return False
                else:
                    print("   ❌ Failed to update .env file")
                    return False
            else:
                print("   ❌ Invalid API key format")
                return False
        else:
            print("   ❌ No API key provided")
            return False
    
    print("\n💡 Manual fix required. Please follow the steps above.")
    return False

def validate_api_key_format(api_key):
    """Valida el formato de la API key"""
    if not api_key:
        return False
    
    # Must start with sk-
    if not api_key.startswith('sk-'):
        print(f"   ❌ API key must start with 'sk-', got: {api_key[:10]}...")
        return False
    
    # Reasonable length
    if len(api_key) < 40:
        print(f"   ❌ API key too short: {len(api_key)} characters")
        return False
    
    print(f"   ✅ API key format looks valid")
    return True

def test_api_key(api_key):
    """Prueba una API key"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        
        return True
        
    except openai.AuthenticationError:
        print("   ❌ Authentication failed - invalid key")
        return False
    except openai.RateLimitError:
        print("   ⚠️ Rate limited but key is valid")
        return True
    except openai.InsufficientQuotaError:
        print("   ⚠️ No credits but key is valid")
        return True
    except Exception as e:
        print(f"   ❌ Error testing key: {e}")
        return False

def update_env_file(env_file_path, new_api_key):
    """Actualiza el archivo .env con la nueva API key"""
    try:
        # Read current .env
        env_content = []
        api_key_updated = False
        
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                env_content = f.readlines()
        
        # Update or add API key
        new_content = []
        for line in env_content:
            if line.strip().startswith('OPENAI_API_KEY='):
                new_content.append(f'OPENAI_API_KEY={new_api_key}\n')
                api_key_updated = True
            else:
                new_content.append(line)
        
        # If not found, add it
        if not api_key_updated:
            new_content.append(f'OPENAI_API_KEY={new_api_key}\n')
        
        # Write back
        with open(env_file_path, 'w') as f:
            f.writelines(new_content)
        
        print(f"   ✅ Updated {env_file_path}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating .env file: {e}")
        return False

def create_env_template_if_missing():
    """Crea un archivo .env template si no existe"""
    project_root = Path(__file__).parent.parent if '__file__' in globals() else Path('.')
    env_file = project_root / '.env'
    
    if not env_file.exists():
        print(f"\n📝 Creating .env template at: {env_file}")
        
        env_template = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration  
SIMPLE_MODEL=gpt-4o-mini
COMPLEX_MODEL=gpt-4o
DEFAULT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# RAG Configuration
CHUNK_SIZE=2200
CHUNK_OVERLAP=440
MAX_DOCUMENTS=10

# Paths
DOCUMENTS_PATH=./data/documents
VECTOR_DB_PATH=./data/vector_db
TRACE_DB_PATH=./data/traces.db

# Logging
LOG_LEVEL=INFO

# UI Configuration
SHARE_GRADIO=false
SERVER_PORT=7860
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_template)
            print("   ✅ .env template created")
            print("   📝 Please edit .env and add your OpenAI API key")
            return True
        except Exception as e:
            print(f"   ❌ Error creating .env: {e}")
            return False
    
    return True

def main():
    """Función principal para arreglar el bug de API key"""
    print("🚀 RAG SYSTEM - API KEY BUG FIX")
    print("=" * 35)
    
    # Ensure .env exists
    create_env_template_if_missing()
    
    # Fix the API key issue
    success = fix_api_key_bug()
    
    if success:
        print("\n" + "=" * 40)
        print("🎉 BUG #1 FIXED SUCCESSFULLY!")
        print("✅ API key is now working")
        print("🚀 Ready to proceed to BUG #2")
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("❌ BUG #1 NOT FIXED")
        print("📋 Please follow the manual steps above")
        print("🔄 Run this script again after updating your API key")
        print("=" * 40)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)