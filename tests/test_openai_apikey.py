import os
import openai
from dotenv import load_dotenv

# Carga variables de entorno desde .env
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print('❌ No se encontró la variable OPENAI_API_KEY en .env')
    exit(1)

openai.api_key = api_key

try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "¿Puedes responderme?"}]
    )
    print('✅ API key válida. Respuesta ejemplo:')
    print(response['choices'][0]['message']['content'])
except openai.error.AuthenticationError as e:
    print('❌ API key inválida o sin permisos:', e)
except Exception as e:
    print('❌ Error al probar la API key:', e)
