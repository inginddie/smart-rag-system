#!/usr/bin/env python3
"""
Advanced API Key Debug - Solución definitiva para key persistente inválida
"""

import os
import sys
import json
import importlib
from pathlib import Path

def advanced_api_key_debug():
    """Diagnóstico avanzado del problema de API key"""
    print("🔍 ADVANCED API KEY DEBUGGING")
    print("=" * 40)
    
    # Setup
    project_root = Path(__file__).parent.parent if '__file__' in globals() else Path('.')
    sys.path.insert(0, str(project_root))
    
    print(f"📁 Project root: {project_root}")
    
    # STEP 1: Deep environment analysis
    print("\n1️⃣ DEEP ENVIRONMENT ANALYSIS")
    print("-" * 30)
    
    # Check all possible env vars
    env_vars_to_check = [
        'OPENAI_API_KEY',
        'OPENAI_KEY', 
        'OPEN_AI_KEY',
        'OPENAI_TOKEN'
    ]
    
    for var in env_vars_to_check:
        value = os.getenv(var)
        if value:
            print(f"   🔍 {var}: {value[:15]}...{value[-8:]} (len: {len(value)})")
        else:
            print(f"   ❌ {var}: Not set")
    
    # STEP 2: File system analysis
    print("\n2️⃣ FILE SYSTEM ANALYSIS")
    print("-" * 25)
    
    config_files = [
        '.env',
        '.env.local',
        '.env.development',
        'config.template',
        '.env.template'
    ]
    
    for config_file in config_files:
        file_path = project_root / config_file
        if file_path.exists():
            print(f"   📄 {config_file}: EXISTS")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for API key lines
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'OPENAI_API_KEY' in line and not line.strip().startswith('#'):
                        # Extract the key value
                        if '=' in line:
                            key_part = line.split('=', 1)[1].strip()
                            # Remove quotes if present
                            key_part = key_part.strip('"\'')
                            print(f"      Line {i}: {key_part[:15]}...{key_part[-8:]} (len: {len(key_part)})")
                            
                            # Check for invisible characters
                            if len(key_part.encode('utf-8')) != len(key_part):
                                print(f"      ⚠️ INVISIBLE CHARACTERS DETECTED!")
                            
                            # Check for whitespace
                            if key_part != key_part.strip():
                                print(f"      ⚠️ WHITESPACE DETECTED!")
                        
            except Exception as e:
                print(f"      ❌ Error reading: {e}")
        else:
            print(f"   ❌ {config_file}: NOT FOUND")
    
    # STEP 3: Settings module analysis
    print("\n3️⃣ SETTINGS MODULE ANALYSIS")
    print("-" * 28)
    
    try:
        # Force reload settings
        if 'config.settings' in sys.modules:
            importlib.reload(sys.modules['config.settings'])
        
        from config.settings import settings
        
        api_key = settings.openai_api_key
        print(f"   📋 Settings API key: {api_key[:15]}...{api_key[-8:]} (len: {len(api_key)})")
        
        # Check encoding
        try:
            api_key_bytes = api_key.encode('utf-8')
            print(f"   📏 UTF-8 bytes: {len(api_key_bytes)}")
            
            # Look for problematic characters
            non_ascii = [c for c in api_key if ord(c) > 127]
            if non_ascii:
                print(f"   ⚠️ Non-ASCII characters found: {non_ascii}")
            
        except Exception as e:
            print(f"   ❌ Encoding error: {e}")
        
        # Check for invisible characters
        cleaned_key = ''.join(c for c in api_key if c.isprintable())
        if len(cleaned_key) != len(api_key):
            print(f"   ⚠️ NON-PRINTABLE CHARACTERS DETECTED!")
            print(f"   🧹 Cleaned key: {cleaned_key[:15]}...{cleaned_key[-8:]}")
        
    except Exception as e:
        print(f"   ❌ Settings error: {e}")
    
    # STEP 4: Manual key testing
    print("\n4️⃣ MANUAL KEY TESTING")
    print("-" * 22)
    
    print("   📝 Please provide your API key for testing:")
    print("   💡 Copy directly from OpenAI dashboard")
    
    manual_key = input("\n🔑 Paste your API key here: ").strip()
    
    if manual_key:
        print(f"\n   📋 Manual key: {manual_key[:15]}...{manual_key[-8:]} (len: {len(manual_key)})")
        
        # Test this key
        if test_manual_key(manual_key):
            print("   ✅ MANUAL KEY WORKS!")
            
            # Compare with settings key
            if manual_key == api_key:
                print("   🤔 Manual key same as settings - config issue?")
            else:
                print("   🔍 Manual key DIFFERENT from settings!")
                print("   💡 Updating configuration...")
                
                if update_all_configs(project_root, manual_key):
                    print("   ✅ Configuration updated!")
                    return True
                else:
                    print("   ❌ Failed to update configuration")
                    return False
        else:
            print("   ❌ Manual key also doesn't work")
            print("   💡 There might be an account issue")
    
    return False

def test_manual_key(api_key):
    """Test a manually provided API key"""
    try:
        import openai
        
        # Clean the key
        clean_key = api_key.strip().strip('"\'')
        
        client = openai.OpenAI(api_key=clean_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print(f"   🎉 Test successful: {response.choices[0].message.content}")
        return True
        
    except openai.AuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Other error: {e}")
        return False

def update_all_configs(project_root, new_key):
    """Update all configuration files with the working key"""
    try:
        # Update .env
        env_file = project_root / '.env'
        
        # Read current content
        env_content = []
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.readlines()
        
        # Update or add the key
        updated = False
        new_content = []
        
        for line in env_content:
            if line.strip().startswith('OPENAI_API_KEY='):
                new_content.append(f'OPENAI_API_KEY={new_key}\n')
                updated = True
                print(f"   ✏️ Updated existing line in .env")
            else:
                new_content.append(line)
        
        if not updated:
            new_content.append(f'OPENAI_API_KEY={new_key}\n')
            print(f"   ➕ Added new line to .env")
        
        # Write back
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_content)
        
        print(f"   💾 Saved to: {env_file}")
        
        # Also set environment variable for immediate use
        os.environ['OPENAI_API_KEY'] = new_key
        print(f"   🔄 Updated environment variable")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating configs: {e}")
        return False

def verify_fix():
    """Verify that the fix worked"""
    print("\n5️⃣ VERIFICATION")
    print("-" * 15)
    
    try:
        # Force reload settings
        if 'config.settings' in sys.modules:
            importlib.reload(sys.modules['config.settings'])
        
        from config.settings import settings
        
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Success test"}],
            max_tokens=10
        )
        
        print("   ✅ VERIFICATION SUCCESSFUL!")
        print(f"   📝 Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ADVANCED API KEY DEBUGGING")
    print("=" * 35)
    
    if advanced_api_key_debug():
        if verify_fix():
            print("\n" + "=" * 40)
            print("🎉 BUG #1 DEFINITIVELY FIXED!")
            print("✅ API key is now working correctly")
            print("🔄 Settings reloaded and verified")
            print("🚀 Ready for BUG #2")
            print("=" * 40)
            return True
    
    print("\n" + "=" * 40)
    print("❌ BUG #1 STILL NOT FIXED")
    print("📞 Possible next steps:")
    print("   1. Check OpenAI account status")
    print("   2. Try creating a fresh API key")
    print("   3. Verify billing/credits")
    print("   4. Contact OpenAI support")
    print("=" * 40)
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)