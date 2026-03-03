# NutriScan AI - PRD (Product Requirements Document)

## Original Problem Statement
Web App para escanear etiquetas alimenticias con análisis de IA (Gemini 3 Flash). Sistema de cuentas con perfil completo (alergias, condiciones, peso, altura, sexo, actividad, objetivo). Chat persistente con IA en pantalla de resultados, con personalidad basada en "Nivel de Exigencia" del usuario.

## User Personas
- **Usuario Principal**: Consumidores que analizan etiquetas nutricionales
- **Usuario con Restricciones**: Celiacos, diabéticos, alérgicos que necesitan alertas personalizadas
- **Usuario Fitness**: Personas con objetivos de pérdida de peso o ganancia muscular

## Core Requirements Implemented

### ✅ Análisis de Etiquetas
- Botón de escaneo con cámara trasera (`capture="environment"`)
- Opción de subir desde galería
- Análisis REAL con Gemini 3 Flash
- Resultados: Health Score, nutrientes, ingredientes, advertencias, recomendaciones

### ✅ Sistema de Cuentas
- Registro con perfil completo en 3 pasos
- Login con tokens persistentes
- Perfil editable con campos:
  - Peso, altura, sexo
  - Alergias (gluten, lactosa, frutos secos, huevo, mariscos, soja, pescado)
  - Condiciones (celiaco, diabético, hipertenso, colesterol)
  - Nivel de actividad (sedentario → muy activa)
  - Objetivo (perder peso, mantener, ganar músculo, mejorar salud)
  - **Nivel de Exigencia** (relajado, normal, estricto, sin filtros)

### ✅ Alertas Personalizadas
- Detección automática de alérgenos en ingredientes
- Alertas para celiacos (gluten)
- Alertas para diabéticos (azúcar)
- Alertas para hipertensos (sodio)

### ✅ Chat IA Persistente (NUEVO)
- Componente de chat estilo WhatsApp en pantalla de resultados
- Burbujas de usuario (verde) y asistente (gris)
- Preguntas sugeridas para iniciar conversación
- Contexto multimodal: imagen + análisis + perfil del usuario
- Historial de chat persistente en MongoDB
- **Personalidad según Nivel de Exigencia**:
  - Relajado: Consejos suaves y comprensivos
  - Normal: Información equilibrada
  - Estricto: Críticas honestas y directas
  - Sin filtros: La verdad cruda sobre la comida (sarcasmo incluido)

## API Endpoints

### Auth
- `POST /api/auth/register` - Registro con perfil
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Cerrar sesión
- `GET /api/auth/me` - Usuario actual
- `PUT /api/auth/profile` - Actualizar perfil

### Analysis
- `POST /api/analyze` - Analizar etiqueta con Gemini 3 Flash
- `GET /api/history` - Historial de escaneos

### Chat
- `POST /api/chat` - Enviar mensaje (multimodal)
- `GET /api/chat/{analysis_id}` - Obtener historial de chat

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI + MongoDB
- IA: Gemini 3 Flash via emergentintegrations
- Despliegue: Compatible con Vercel

## Next Tasks
1. Crear páginas legales (Privacidad, Términos) para AdSense
2. PWA para instalación en móvil
3. Añadir historial de escaneos en UI
4. Compartir resultados
