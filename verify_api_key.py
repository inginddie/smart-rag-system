#!/usr/bin/env python3
"""
Verificador de API Key - Ejecuta esto después de hacer los cambios
"""
import os
from config.settings import Settings

print("=== VERIFICACIÓN FINAL DE API KEY ===")
print()

# Check sources
env_key = os.environ.get('OPENAI_API_KEY', 'NOT SET')
print(f"1. Variable de entorno: {env_key}")

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            env_file_key = line.split('=', 1)[1].strip()
            print(f"2. Archivo .env: {env_file_key}")
            break

settings = Settings()
print(f"3. Settings carga: {settings.openai_api_key}")

print()
if settings.openai_api_key == "tu_api_key_aqui":
    print("✅ CORRECTO: El sistema ahora usará tu API key del archivo .env")
    print("📝 Por favor edita .env y pon tu API key real de OpenAI")
elif not settings.openai_api_key:
    print("✅ CORRECTO: No hay API key configurada")
    print("📝 Por favor edita .env y pon tu API key de OpenAI")
else:
    print("⚠️ ATENCIÓN: Aún hay una API key configurada")
    print("🔄 Puede ser que necesites reiniciar tu terminal")