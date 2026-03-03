# NutriScan AI - PRD (Product Requirements Document)

## Original Problem Statement
Crear una Web App con React y Tailwind CSS para escanear etiquetas alimenticias. Diseño limpio con tema oscuro, botón grande "Escanear Etiqueta". Al pulsarlo, debe abrir la cámara del móvil (con capture='environment') o permitir subir una foto. Análisis con Gemini 3 Flash. Sistema de cuentas con perfil de usuario (alergias, condiciones, peso, altura, sexo). Alertas personalizadas basadas en el perfil. Footer preparado para Google AdSense.

## User Personas
- **Usuario Principal**: Consumidores conscientes de su salud que desean analizar etiquetas nutricionales
- **Usuario con Alergias**: Personas con alergias alimentarias (gluten, lactosa, frutos secos, etc.)
- **Usuario con Condiciones**: Personas con diabetes, celiaquía, hipertensión que necesitan vigilar nutrientes específicos

## Core Requirements
1. ✅ Tema oscuro (Cyber-Health aesthetic)
2. ✅ Idioma español
3. ✅ Botón grande de escaneo con animación neon glow
4. ✅ Modal de cámara con `capture="environment"` para cámara trasera
5. ✅ Opción de subir desde galería
6. ✅ Análisis REAL con Gemini 3 Flash
7. ✅ Sistema de autenticación (registro/login)
8. ✅ Perfil de usuario con peso, altura, sexo
9. ✅ Selección de alergias (gluten, lactosa, frutos secos, huevo, mariscos, soja, pescado)
10. ✅ Selección de condiciones (celiaco, diabético, hipertenso, colesterol)
11. ✅ Alertas personalizadas basadas en perfil
12. ✅ Footer con enlaces legales para AdSense

## What's Been Implemented (Date: 2026-03-03)

### Backend (FastAPI)
- `POST /api/auth/register` - Registro con perfil completo
- `POST /api/auth/login` - Login con token
- `POST /api/auth/logout` - Cerrar sesión
- `GET /api/auth/me` - Obtener usuario actual
- `PUT /api/auth/profile` - Actualizar perfil
- `POST /api/analyze` - Análisis de etiquetas con Gemini 3 Flash REAL
- `GET /api/history` - Historial de escaneos

### Frontend (React + Tailwind)
- **AuthProvider**: Contexto global de autenticación
- **Landing Page**: Hero con botón de escaneo, features, CTA para registro
- **AuthModal**: 3 pasos de registro (credenciales → perfil → alergias/condiciones)
- **ProfileModal**: Edición de perfil completo
- **CameraModal**: 
  - Botón "Cámara" con `capture="environment"`
  - Botón "Galería" para subir desde archivos
  - Vista previa de imagen
  - Animación de escaneo durante análisis
- **ResultsView**: 
  - Alertas personalizadas según perfil del usuario
  - Info del producto (nombre, marca, porción)
  - Health Score circular
  - Tarjetas de nutrientes con barras de progreso
  - Lista de ingredientes
  - Advertencias y recomendaciones

### Alertas Personalizadas
El sistema genera alertas automáticas cuando:
- **Alergias**: Detecta ingredientes relacionados con las alergias del usuario
- **Celiaco**: Alerta si contiene gluten, trigo, cebada, centeno
- **Diabético**: Alerta si tiene alto contenido de azúcar
- **Hipertenso**: Alerta si tiene alto contenido de sodio

## Prioritized Backlog

### P0 (Completado)
- ✅ Análisis con IA real (Gemini 3 Flash)
- ✅ Sistema de cuentas
- ✅ Alertas personalizadas

### P1 (Alta prioridad)
- [ ] Páginas legales completas (Privacidad, Términos, Contacto)
- [ ] Historial de escaneos en UI
- [ ] PWA para instalación en móvil

### P2 (Media prioridad)
- [ ] Guardar productos favoritos
- [ ] Comparar productos
- [ ] Compartir resultados

### P3 (Baja prioridad)
- [ ] Modo offline
- [ ] Notificaciones push
- [ ] Multi-idioma

## Next Tasks
1. Crear páginas legales completas para cumplir requisitos de AdSense
2. Añadir vista de historial de escaneos
3. Implementar PWA para mejor experiencia móvil
