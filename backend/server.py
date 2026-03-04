from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import uuid
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import google.generativeai as genai

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'nutriscan_db')]

# Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserProfile(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    sex: Optional[str] = None
    allergies: List[str] = []
    conditions: List[str] = []
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    strictness_level: Optional[str] = "normal"

class NutrientInfo(BaseModel):
    name: str
    value: str
    unit: str
    percentage: Optional[int] = None
    status: str = "normal"

class PersonalizedAlert(BaseModel):
    type: str
    message: str
    related_to: str

class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    brand: str
    serving_size: str
    health_score: int
    nutrients: List[NutrientInfo]
    ingredients: List[str]
    warnings: List[str]
    recommendations: List[str]
    personalized_alerts: List[PersonalizedAlert] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None

class AnalyzeRequest(BaseModel):
    image_base64: str

class ChatRequest(BaseModel):
    analysis_id: str
    message: str
    image_base64: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GeneralChatRequest(BaseModel):
    message: str
    user_profile: Optional[dict] = None

# ==================== AUTH (SUPABASE JWT) ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """
    El frontend ya usa Supabase para auth.
    Aquí simplemente leemos el user_id del token JWT de Supabase
    sin verificar firma (confiamos en que Supabase lo emitió).
    Para producción puedes añadir verificación con python-jose.
    """
    if not credentials:
        return None
    try:
        import base64
        token = credentials.credentials
        # Decode payload (middle part of JWT)
        payload_b64 = token.split('.')[1]
        # Add padding if needed
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
        }
    except Exception:
        return None

# ==================== HELPERS ====================

def generate_personalized_alerts(
    user_profile: UserProfile,
    ingredients: List[str],
    nutrients: List[NutrientInfo]
) -> List[PersonalizedAlert]:
    alerts = []
    ingredients_text = " ".join(i.lower() for i in ingredients)

    allergy_keywords = {
        "gluten": ["gluten", "trigo", "wheat", "cebada", "centeno", "avena"],
        "lactose": ["leche", "lactosa", "milk", "suero", "whey", "caseína"],
        "nuts": ["nuez", "almendra", "avellana", "pistacho", "anacardo", "cacahuete"],
        "eggs": ["huevo", "egg", "albúmina"],
        "shellfish": ["marisco", "camarón", "langosta", "cangrejo"],
        "soy": ["soja", "soy", "lecitina de soja"],
        "fish": ["pescado", "fish", "anchoa", "atún"],
    }

    for allergy in user_profile.allergies:
        keywords = allergy_keywords.get(allergy.lower(), [allergy.lower()])
        for kw in keywords:
            if kw in ingredients_text:
                alerts.append(PersonalizedAlert(
                    type="danger",
                    message=f"⚠️ ALERTA: Este producto puede contener {allergy.upper()}",
                    related_to=f"allergy:{allergy}"
                ))
                break

    for nutrient in nutrients:
        name = nutrient.name.lower()
        try:
            value = float(nutrient.value.replace(",", "."))
        except ValueError:
            continue

        if "diabetic" in [c.lower() for c in user_profile.conditions]:
            if "azúcar" in name or "sugar" in name:
                if value > 5:
                    alerts.append(PersonalizedAlert(
                        type="warning",
                        message=f"Alto contenido de azúcar ({nutrient.value}{nutrient.unit}). Precaución para diabéticos.",
                        related_to="condition:diabetes"
                    ))

        if "hypertensive" in [c.lower() for c in user_profile.conditions]:
            if "sodio" in name or "sodium" in name:
                if value > 400:
                    alerts.append(PersonalizedAlert(
                        type="warning",
                        message=f"Alto contenido de sodio ({nutrient.value}{nutrient.unit}). Precaución para hipertensos.",
                        related_to="condition:hypertension"
                    ))

    if "celiac" in [c.lower() for c in user_profile.conditions]:
        for kw in ["gluten", "trigo", "wheat", "cebada", "centeno"]:
            if kw in ingredients_text:
                alerts.append(PersonalizedAlert(
                    type="danger",
                    message="⚠️ ALERTA CELIACO: Este producto contiene GLUTEN",
                    related_to="condition:celiac"
                ))
                break

    return alerts


def get_personality_prompt(strictness: str) -> str:
    personalities = {
        "relaxed": "Eres un nutricionista amigable y comprensivo. Da consejos suaves y positivos.",
        "normal": "Eres un nutricionista profesional y equilibrado. Da información objetiva.",
        "strict": "Eres un nutricionista estricto y directo. Sé honesto sobre los aspectos negativos.",
        "very_strict": "Eres un nutricionista sin filtros. Sé brutalmente honesto. Si algo es malo para la salud, dilo claramente.",
    }
    return personalities.get(strictness, personalities["normal"])


async def analyze_with_gemini(
    image_base64: str,
    user_profile: Optional[UserProfile] = None
) -> AnalysisResult:
    import base64

    user_context = ""
    if user_profile:
        if user_profile.allergies:
            user_context += f"\nAlergias del usuario: {', '.join(user_profile.allergies)}"
        if user_profile.conditions:
            user_context += f"\nCondiciones: {', '.join(user_profile.conditions)}"

    prompt = f"""Eres un experto nutricionista. Analiza esta etiqueta nutricional.

RESPONDE SOLO EN JSON con esta estructura exacta (sin markdown, sin texto extra):
{{
    "product_name": "nombre del producto",
    "brand": "marca o Desconocida",
    "serving_size": "tamaño de porción",
    "health_score": número 0-100,
    "nutrients": [
        {{"name": "Calorías", "value": "valor", "unit": "kcal", "percentage": null, "status": "normal"}},
        {{"name": "Grasas Totales", "value": "valor", "unit": "g", "percentage": null, "status": "normal"}},
        {{"name": "Grasas Saturadas", "value": "valor", "unit": "g", "percentage": null, "status": "normal"}},
        {{"name": "Carbohidratos", "value": "valor", "unit": "g", "percentage": null, "status": "normal"}},
        {{"name": "Azúcares", "value": "valor", "unit": "g", "percentage": null, "status": "warning"}},
        {{"name": "Fibra", "value": "valor", "unit": "g", "percentage": null, "status": "good"}},
        {{"name": "Proteínas", "value": "valor", "unit": "g", "percentage": null, "status": "good"}},
        {{"name": "Sodio", "value": "valor", "unit": "mg", "percentage": null, "status": "normal"}}
    ],
    "ingredients": ["ingrediente1", "ingrediente2"],
    "warnings": ["advertencia1"],
    "recommendations": ["recomendación1"]
}}

Status: good=saludable, warning=moderado, danger=preocupante, normal=ok
Health score: 80-100 muy saludable, 60-79 moderado, 40-59 mejorable, 0-39 poco recomendable
{user_context}"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        image_data = base64.b64decode(image_base64)
        image_part = {"mime_type": "image/jpeg", "data": image_data}
        response = model.generate_content([prompt, image_part])
        
        text = response.text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        data = json.loads(text)

        nutrients = [
            NutrientInfo(
                name=n["name"],
                value=str(n["value"]),
                unit=n["unit"],
                percentage=n.get("percentage"),
                status=n.get("status", "normal")
            )
            for n in data.get("nutrients", [])
        ]

        personalized_alerts = []
        if user_profile:
            personalized_alerts = generate_personalized_alerts(
                user_profile, data.get("ingredients", []), nutrients
            )

        return AnalysisResult(
            product_name=data.get("product_name", "Producto desconocido"),
            brand=data.get("brand", "Desconocida"),
            serving_size=data.get("serving_size", "No especificado"),
            health_score=int(data.get("health_score", 50)),
            nutrients=nutrients,
            ingredients=data.get("ingredients", []),
            warnings=data.get("warnings", []),
            recommendations=data.get("recommendations", []),
            personalized_alerts=personalized_alerts
        )

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {str(e)}")


# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "NutriScan API funcionando ✅"}

@api_router.post("/analyze", response_model=AnalysisResult)
async def analyze_label(
    request: AnalyzeRequest,
    user: Optional[dict] = Depends(get_current_user)
):
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="Se requiere imagen")

    user_profile = None
    user_id = None

    if user:
        user_id = user["id"]
        # Fetch profile from MongoDB if exists
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user_doc and user_doc.get("profile"):
            user_profile = UserProfile(**user_doc["profile"])

    result = await analyze_with_gemini(request.image_base64, user_profile)
    result.user_id = user_id

    doc = result.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.scan_history.insert_one(doc)

    return result


@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    user: Optional[dict] = Depends(get_current_user)
):
    analysis = await db.scan_history.find_one({"id": request.analysis_id}, {"_id": 0})
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")

    strictness = "normal"
    user_context = ""
    if user:
        user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0})
        if user_doc:
            profile = user_doc.get("profile", {})
            strictness = profile.get("strictness_level", "normal")

    personality = get_personality_prompt(strictness)

    nutrients_text = "\n".join(
        f"- {n['name']}: {n['value']} {n['unit']}"
        for n in analysis.get("nutrients", [])
    )

    system = f"""{personality}

PRODUCTO: {analysis.get('product_name')} ({analysis.get('brand')})
Puntuación: {analysis.get('health_score')}/100
NUTRIENTES:
{nutrients_text}
INGREDIENTES: {', '.join(analysis.get('ingredients', []))}

Responde en español, máximo 3-4 frases. Sé directo y útil."""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system)
        response = model.generate_content(request.message)

        # Save to chat history
        await db.chat_history.update_one(
            {"analysis_id": request.analysis_id},
            {"$push": {"messages": {"$each": [
                {"role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc).isoformat()},
                {"role": "assistant", "content": response.text, "timestamp": datetime.now(timezone.utc).isoformat()}
            ]}}},
            upsert=True
        )

        return ChatResponse(response=response.text)

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en el chat: {str(e)}")


@api_router.get("/chat/{analysis_id}")
async def get_chat_history(
    analysis_id: str,
    user: dict = Depends(get_current_user)
):
    chat_doc = await db.chat_history.find_one({"analysis_id": analysis_id}, {"_id": 0})
    if not chat_doc:
        return {"messages": []}
    return {"messages": chat_doc.get("messages", [])}


@api_router.post("/general-chat")
async def general_chat(request: GeneralChatRequest):
    strictness = "normal"
    user_context = ""

    if request.user_profile:
        profile = request.user_profile
        strictness = profile.get("strictness_level", "normal")
        if profile.get("goal"):
            goal_map = {"lose_weight": "Perder peso", "maintain": "Mantener", "gain_muscle": "Ganar músculo", "health": "Mejorar salud"}
            user_context += f"\nObjetivo: {goal_map.get(profile['goal'], profile['goal'])}"
        if profile.get("allergies"):
            user_context += f"\nAlergias: {', '.join(profile['allergies'])}"
        if profile.get("conditions"):
            user_context += f"\nCondiciones: {', '.join(profile['conditions'])}"

    personality = get_personality_prompt(strictness)
    system = f"""{personality}
Eres NutriScan AI, asistente experto en nutrición.
{user_context}
Responde en español, máximo 3-4 frases. No des consejos médicos específicos."""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system)
        response = model.generate_content(request.message)
        return {"response": response.text}

    except Exception as e:
        logger.error(f"General chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ==================== APP SETUP ====================

app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown():
    client.close()
```

---

Ahora actualiza también `backend/requirements.txt` con este contenido:
```
fastapi==0.111.0
uvicorn==0.30.1
motor==3.4.0
python-dotenv==1.0.1
google-generativeai==0.7.2
pydantic==2.7.1
python-jose==3.3.0
httpx==0.27.0
```

---

Y el `backend/.env` local (nunca lo subas a GitHub):
```
MONGO_URL=tu_mongo_url_de_atlas
DB_NAME=nutriscan_db
GEMINI_API_KEY=tu_api_key_de_gemini
```

---

## Ahora los pasos para desplegarlo en Render

**Paso 1 — Consigue tu Gemini API Key gratis**
Ve a [aistudio.google.com](https://aistudio.google.com) → "Get API Key" → copia la key.

**Paso 2 — Crea cuenta en Render**
Ve a [render.com](https://render.com) → regístrate con tu GitHub.

**Paso 3 — Nuevo Web Service**
- "New" → "Web Service" → conecta tu repo de GitHub
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

**Paso 4 — Variables de entorno en Render**
En el panel de Render añade:
```
MONGO_URL        = tu_mongo_connection_string
DB_NAME          = nutriscan_db
GEMINI_API_KEY   = tu_key_de_gemini
```

**Paso 5 — Actualiza el frontend**
Una vez Render te dé la URL (algo como `https://nutriscan-api.onrender.com`), actualiza en Vercel:
```
REACT_APP_BACKEND_URL=https://nutriscan-api.onrender.com