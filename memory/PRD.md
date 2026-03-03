# NutriScan AI - PRD (Product Requirements Document)

## Original Problem Statement
Crear una Web App con Vite + React y Tailwind CSS para escanear etiquetas alimenticias. Diseño limpio con tema oscuro, botón grande "Escanear Etiqueta". Al pulsarlo, debe abrir la cámara del móvil o permitir subir una foto. Simular análisis con mensaje de carga y mostrar resultado de ejemplo profesional. Incluir Navbar y Footer preparado para enlaces legales de Google AdSense.

## User Personas
- **Usuario Principal**: Consumidores conscientes de su salud que desean analizar etiquetas nutricionales de productos alimenticios antes de comprarlos o consumirlos.
- **Usuario Secundario**: Personas con restricciones dietéticas (diabéticos, celíacos, etc.) que necesitan verificar ingredientes rápidamente.

## Core Requirements
1. ✅ Tema oscuro (Cyber-Health aesthetic)
2. ✅ Idioma español
3. ✅ Botón grande de escaneo con animación
4. ✅ Modal de cámara/subida de imagen
5. ✅ Estado de carga con animación de escaneo
6. ✅ Resultados profesionales con información nutricional
7. ✅ Navbar con logo NutriScan
8. ✅ Footer con enlaces legales para AdSense
9. ✅ Preparado para integración con Gemini 3 Flash

## What's Been Implemented (Date: 2026-03-03)

### Backend (FastAPI)
- `POST /api/analyze` - Análisis de etiquetas (actualmente SIMULADO)
- `GET /api/history` - Historial de escaneos
- `GET/POST /api/status` - Health check
- EMERGENT_LLM_KEY configurado para futura integración Gemini

### Frontend (React + Tailwind)
- **Landing Page**: Hero con imagen de fondo, botón de escaneo animado, 3 features
- **Camera Modal**: Viewfinder con corners, subida de imagen, botón "Usar ejemplo"
- **Results View**: 
  - Info del producto (nombre, marca, porción)
  - Health Score circular (0-100)
  - 8 tarjetas de nutrientes con barras de progreso
  - Sección de advertencias
  - Sección de recomendaciones
- **Navbar**: Logo NutriScan, menú hamburguesa
- **Footer**: Enlaces a Privacidad, Términos, Contacto

### Design System
- Colors: Zinc-950 bg, Green-600 primary, Yellow warning, Red danger
- Fonts: Manrope (headings), Inter (body), JetBrains Mono (code)
- Animations: Scan line, pulse glow, fade-in-up, shimmer
- Glassmorphism + neon glow effects

## Mocked/Simulated APIs
- ⚠️ **POST /api/analyze**: Retorna datos simulados de "Galletas Integrales de Avena" con 8 nutrientes, 3 advertencias y 3 recomendaciones. Preparado para integrar Gemini 3 Flash.

## Prioritized Backlog

### P0 (Bloqueantes)
- Ninguno - MVP completado

### P1 (Alta prioridad)
- [ ] Integrar Gemini 3 Flash para análisis real de imágenes
- [ ] Añadir captura de cámara nativa (navigator.mediaDevices)
- [ ] Páginas de Política de Privacidad, Términos y Contacto completas

### P2 (Media prioridad)
- [ ] Historial de escaneos en UI
- [ ] Guardar productos favoritos
- [ ] Comparar productos

### P3 (Baja prioridad)
- [ ] PWA (Progressive Web App) para instalación
- [ ] Modo offline con últimos escaneos
- [ ] Compartir resultados

## Next Tasks
1. Activar integración real con Gemini 3 Flash para análisis de imágenes
2. Crear páginas legales completas (Privacy, Terms, Contact) para AdSense
3. Añadir historial de escaneos visible en la UI
