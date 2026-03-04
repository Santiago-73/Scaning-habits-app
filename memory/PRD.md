# NutriScan AI - PRD (Product Requirements Document)

## Última Actualización: 2026-03-03

## Resumen de Cambios
- ✅ Migración a Supabase Auth
- ✅ Chat general accesible desde pantalla principal
- ✅ Perfiles de usuario en localStorage

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (para análisis y chat)
- **Auth**: Supabase Auth (registro/login)
- **IA**: Gemini 3 Flash via emergentintegrations
- **Perfiles**: localStorage (nutriscan_profile_{userId})

## Variables de Entorno (para Vercel)

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://tu-backend-url.com
REACT_APP_SUPABASE_URL=https://grchmdtogimkpchswxig.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Backend (.env)
```
MONGO_URL=tu-mongodb-url
DB_NAME=nutriscan_db
EMERGENT_LLM_KEY=tu-emergent-key
```

## Funcionalidades Implementadas

### 1. Autenticación (Supabase)
- `supabase.auth.signUp()` - Registro de usuarios
- `supabase.auth.signInWithPassword()` - Login
- `supabase.auth.signOut()` - Logout
- Perfiles guardados en localStorage

### 2. Escáner de Etiquetas
- Cámara trasera (`capture="environment"`)
- Subida desde galería
- Análisis con Gemini 3 Flash
- Resultados: nutrientes, ingredientes, advertencias, recomendaciones
- Health Score (0-100)

### 3. Chat IA en Análisis
- Contexto: imagen + análisis + perfil usuario
- Preguntas de seguimiento sobre el producto
- Historial persistente en MongoDB

### 4. Chat General (NUEVO)
- Botón flotante en pantalla principal
- Preguntas generales sobre nutrición
- Respuestas personalizadas según perfil
- Endpoint: POST /api/general-chat

### 5. Alertas Personalizadas
- Detección de alérgenos
- Alertas para: celiacos, diabéticos, hipertensos
- Basadas en perfil del usuario

### 6. Nivel de Exigencia (Personalidad IA)
- Relajado: consejos suaves
- Normal: información equilibrada
- Estricto: críticas honestas
- Sin filtros: verdad cruda

## API Endpoints

### Backend (/api)
- `POST /api/analyze` - Analizar etiqueta
- `POST /api/chat` - Chat sobre producto analizado
- `POST /api/general-chat` - Chat general de nutrición
- `GET /api/history` - Historial de escaneos

### Supabase Auth (frontend directo)
- `supabase.auth.signUp()`
- `supabase.auth.signInWithPassword()`
- `supabase.auth.signOut()`
- `supabase.auth.getSession()`

## Archivos Clave
- `/app/frontend/src/App.js` - Aplicación principal
- `/app/frontend/src/lib/supabase.js` - Cliente Supabase
- `/app/frontend/.env` - Variables de entorno frontend
- `/app/backend/server.py` - API FastAPI
- `/app/backend/.env` - Variables de entorno backend

## Next Tasks
1. Crear páginas legales (Privacidad, Términos)
2. Implementar PWA
3. Añadir historial de escaneos en UI
