import os
from openai import OpenAI
from dotenv import load_dotenv

# Carga variables de entorno desde .env
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print('[ERROR] No se encontro la variable OPENAI_API_KEY en .env')
    exit(1)

client = OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "¿Puedes responderme?"}]
    )
    print('[SUCCESS] API key valida. Respuesta ejemplo:')
    print(response.choices[0].message.content)
except Exception as e:
    if "authentication" in str(e).lower() or "api key" in str(e).lower():
        print('[ERROR] API key invalida o sin permisos:', e)
    else:
        print('[ERROR] Error al probar la API key:', e)
