# 🚀 Cómo Ejecutar la Aplicación

## ⚡ Método Rápido (Recomendado)

### 1. Ejecutar el Launcher

```bash
python launch_app.py
```

**Características:**
- ✅ Encuentra puerto libre automáticamente
- ✅ Abre el navegador automáticamente
- ✅ Muestra instrucciones en consola
- ✅ Manejo de errores mejorado

### 2. Acceder a la Aplicación

El navegador se abrirá automáticamente en:
```
http://localhost:XXXX
```
(El puerto se mostrará en la consola)

### 3. Inicializar el Sistema

1. Ve al tab **"⚙️ Administración"**
2. Presiona **"🚀 Inicializar Sistema"**
3. Espera el mensaje: ✅ Sistema RAG inicializado correctamente

### 4. Usar el Panel de Keywords

1. Ve al tab **"🔧 Administración"** (nuevo)
2. Explora las funcionalidades:
   - 📊 Estadísticas del sistema
   - 🧪 Prueba de activación
   - 🎯 Gestión de keywords
   - ⚙️ Configuración de threshold

---

## 🔧 Método Alternativo

### Usando main.py

```bash
python main.py --mode ui
```

**Nota**: Este método usa el puerto configurado en `.env` (por defecto 7860)

---

## 🐛 Solución de Problemas

### Puerto Ocupado

**Síntoma:**
```
OSError: Cannot find empty port in range: 7860-7860
```

**Solución 1**: Usar el launcher (recomendado)
```bash
python launch_app.py
```

**Solución 2**: Cerrar proceso que usa el puerto
```bash
# Windows
netstat -ano | findstr :7860
taskkill /F /PID <PID>

# Linux/Mac
lsof -i :7860
kill -9 <PID>
```

**Solución 3**: Cambiar puerto en `.env`
```env
SERVER_PORT=8080
```

### Error de Módulo

**Síntoma:**
```
ModuleNotFoundError: No module named 'src'
```

**Solución**: Ejecutar desde el directorio raíz del proyecto
```bash
cd C:\Users\Diego\Documents\RAG
python launch_app.py
```

### Panel de Keywords No Aparece

**Síntoma:**
El tab "🔧 Administración" muestra mensaje de inicialización

**Solución:**
1. Ve a "⚙️ Administración"
2. Presiona "🚀 Inicializar Sistema"
3. El panel aparecerá automáticamente

### Error de API Key

**Síntoma:**
```
Error: OpenAI API key not found
```

**Solución:**
1. Copia el template: `cp config.template .env`
2. Edita `.env` y agrega tu API key:
   ```env
   OPENAI_API_KEY=tu_api_key_aqui
   ```

---

## 📋 Checklist Pre-Ejecución

Antes de ejecutar, verifica:

- [ ] Python 3.8+ instalado
- [ ] Dependencias instaladas: `pip install -r requirements.txt`
- [ ] Archivo `.env` configurado con API key
- [ ] Documentos en `data/documents/` (opcional)
- [ ] Puerto libre disponible

---

## 🎯 Flujo Completo de Uso

### 1. Primera Vez

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp config.template .env
# Editar .env con tu API key

# Ejecutar
python launch_app.py
```

### 2. Uso Normal

```bash
# Simplemente ejecutar
python launch_app.py
```

### 3. Después de Inicializar

1. **Chat Académico**: Hacer preguntas sobre documentos
2. **Administración de Keywords**: Gestionar keywords de agentes
3. **Guía de Investigación**: Ver ayuda y ejemplos

---

## 🌐 URLs Importantes

### Aplicación Principal
```
http://localhost:XXXX
```

### Tabs Disponibles

1. **💬 Chat Académico**
   - Hacer preguntas
   - Ver respuestas con agentes
   - Historial de conversación

2. **⚙️ Administración**
   - Inicializar sistema
   - Reindexar documentos
   - Ver configuración

3. **🔧 Administración** (Keywords)
   - Gestionar keywords
   - Probar activación
   - Ajustar thresholds
   - Exportar/importar

4. **📚 Guía de Investigación**
   - Ayuda y ejemplos
   - Tipos de consultas
   - Consejos

---

## 💡 Tips de Uso

### Para Mejor Performance

1. **Coloca documentos antes de inicializar**
   ```bash
   # Copiar PDFs a:
   data/documents/
   ```

2. **Usa el launcher para evitar problemas de puerto**
   ```bash
   python launch_app.py
   ```

3. **Inicializa solo una vez por sesión**
   - No es necesario reinicializar cada vez

### Para Gestión de Keywords

1. **Prueba antes de agregar**
   - Usa "🧪 Prueba de Activación"
   - Verifica el score

2. **Agrega keywords relevantes**
   - Palabras simples
   - Sinónimos en diferentes idiomas
   - Términos de tu dominio

3. **Ajusta threshold según necesites**
   - Bajo (0.1-0.3): Más activaciones
   - Medio (0.4-0.6): Balance
   - Alto (0.7-1.0): Solo queries específicas

---

## 🔄 Reiniciar la Aplicación

### Método 1: Ctrl+C en la consola

```bash
# En la consola donde corre la app
Ctrl+C

# Ejecutar nuevamente
python launch_app.py
```

### Método 2: Cerrar ventana del navegador

La app seguirá corriendo en la consola. Para detenerla:
```bash
Ctrl+C
```

---

## 📊 Verificar que Todo Funciona

### Checklist Post-Inicio

- [ ] Navegador se abre automáticamente
- [ ] URL se muestra en consola
- [ ] Interfaz Gradio carga correctamente
- [ ] Tab "⚙️ Administración" visible
- [ ] Botón "🚀 Inicializar Sistema" funciona
- [ ] Tab "🔧 Administración" aparece después de inicializar
- [ ] Panel de keywords muestra estadísticas
- [ ] Prueba de activación funciona

### Test Rápido

1. **Inicializar**: ✅ Sistema RAG inicializado
2. **Probar query**: "Find research papers"
3. **Ver resultado**: Agente se activa con score > 0.3
4. **Agregar keyword**: "investigar"
5. **Probar nuevamente**: "Quiero investigar"
6. **Verificar**: Nueva keyword detectada

---

## 🎉 ¡Listo!

Si todos los pasos funcionan, tu aplicación está lista para usar.

**Próximos pasos:**
1. Explorar el panel de administración
2. Agregar tus documentos
3. Personalizar keywords
4. Hacer preguntas académicas

---

**Versión**: 2.0.0  
**Última Actualización**: 2025-10-03  
**Estado**: ✅ FUNCIONAL
