from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import hashlib
import secrets
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'nutriscan_db')]

# Gemini integration
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# ==================== MODELS ====================

class UserProfile(BaseModel):
    weight: Optional[float] = None  # kg
    height: Optional[float] = None  # cm
    sex: Optional[str] = None  # male, female, other
    allergies: List[str] = []  # gluten, lactose, nuts, eggs, shellfish, soy, etc.
    conditions: List[str] = []  # celiac, diabetic, hypertensive, etc.
    activity_level: Optional[str] = None  # sedentary, light, moderate, active, very_active
    goal: Optional[str] = None  # lose_weight, maintain, gain_muscle, health
    strictness_level: Optional[str] = "normal"  # relaxed, normal, strict, very_strict

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    profile: Optional[UserProfile] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    profile: UserProfile
    created_at: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile: Optional[UserProfile] = None

class NutrientInfo(BaseModel):
    name: str
    value: str
    unit: str
    percentage: Optional[int] = None
    status: str = "normal"

class PersonalizedAlert(BaseModel):
    type: str  # warning, danger, info
    message: str
    related_to: str  # allergy, condition, nutrient

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

class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    analysis_id: str
    message: str
    image_base64: Optional[str] = None  # Original image for context

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

# ==================== HELPERS ====================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if not credentials:
        return None
    token = credentials.credentials
    session = await db.sessions.find_one({"token": token}, {"_id": 0})
    if not session:
        return None
    user = await db.users.find_one({"id": session["user_id"]}, {"_id": 0})
    return user

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user

def generate_personalized_alerts(user_profile: UserProfile, ingredients: List[str], nutrients: List[NutrientInfo]) -> List[PersonalizedAlert]:
    """Generate alerts based on user's health profile"""
    alerts = []
    ingredients_lower = [i.lower() for i in ingredients]
    ingredients_text = " ".join(ingredients_lower)
    
    # Allergy checks
    allergy_keywords = {
        "gluten": ["gluten", "trigo", "wheat", "cebada", "centeno", "avena", "espelta"],
        "lactose": ["leche", "lactosa", "milk", "lactose", "suero", "whey", "caseína", "casein"],
        "nuts": ["nuez", "nueces", "almendra", "avellana", "pistacho", "anacardo", "cacahuete", "maní", "nut", "almond", "hazelnut"],
        "eggs": ["huevo", "egg", "albúmina", "albumin", "lecitina de huevo"],
        "shellfish": ["marisco", "camarón", "langosta", "cangrejo", "shellfish", "shrimp"],
        "soy": ["soja", "soy", "lecitina de soja"],
        "fish": ["pescado", "fish", "anchoa", "atún"],
    }
    
    for allergy in user_profile.allergies:
        allergy_lower = allergy.lower()
        keywords = allergy_keywords.get(allergy_lower, [allergy_lower])
        for keyword in keywords:
            if keyword in ingredients_text:
                alerts.append(PersonalizedAlert(
                    type="danger",
                    message=f"⚠️ ALERTA: Este producto puede contener {allergy.upper()}",
                    related_to=f"allergy:{allergy}"
                ))
                break
    
    # Condition-based alerts
    for nutrient in nutrients:
        nutrient_name = nutrient.name.lower()
        
        # Diabetic checks
        if "diabetic" in [c.lower() for c in user_profile.conditions] or "diabetes" in [c.lower() for c in user_profile.conditions]:
            if "azúcar" in nutrient_name or "sugar" in nutrient_name:
                try:
                    value = float(nutrient.value.replace(",", "."))
                    if value > 5:
                        alerts.append(PersonalizedAlert(
                            type="warning",
                            message=f"Alto contenido de azúcar ({nutrient.value}{nutrient.unit}). Precaución para diabéticos.",
                            related_to="condition:diabetes"
                        ))
                except:
                    pass
        
        # Hypertensive checks
        if "hypertensive" in [c.lower() for c in user_profile.conditions] or "hipertensión" in [c.lower() for c in user_profile.conditions]:
            if "sodio" in nutrient_name or "sodium" in nutrient_name or "sal" in nutrient_name:
                try:
                    value = float(nutrient.value.replace(",", "."))
                    if value > 400:
                        alerts.append(PersonalizedAlert(
                            type="warning",
                            message=f"Alto contenido de sodio ({nutrient.value}{nutrient.unit}). Precaución para hipertensos.",
                            related_to="condition:hypertension"
                        ))
                except:
                    pass
    
    # Celiac check
    if "celiac" in [c.lower() for c in user_profile.conditions] or "celiaco" in [c.lower() for c in user_profile.conditions]:
        gluten_keywords = ["gluten", "trigo", "wheat", "cebada", "centeno", "espelta"]
        for keyword in gluten_keywords:
            if keyword in ingredients_text:
                alerts.append(PersonalizedAlert(
                    type="danger",
                    message="⚠️ ALERTA CELIACO: Este producto contiene o puede contener GLUTEN",
                    related_to="condition:celiac"
                ))
                break
    
    return alerts

async def analyze_with_gemini(image_base64: str, user_profile: Optional[UserProfile] = None) -> AnalysisResult:
    """Analyze food label image using Gemini 3 Flash"""
    
    # Build context about user if available
    user_context = ""
    if user_profile:
        if user_profile.allergies:
            user_context += f"\nAlergias del usuario: {', '.join(user_profile.allergies)}"
        if user_profile.conditions:
            user_context += f"\nCondiciones de salud: {', '.join(user_profile.conditions)}"
    
    system_prompt = f"""Eres un experto nutricionista que analiza etiquetas de productos alimenticios.
Analiza la imagen de la etiqueta nutricional y extrae TODA la información disponible.

RESPONDE SIEMPRE EN ESPAÑOL y en formato JSON válido con esta estructura exacta:
{{
    "product_name": "nombre del producto",
    "brand": "marca (si visible, sino 'Desconocida')",
    "serving_size": "tamaño de porción",
    "health_score": número del 0 al 100 basado en la calidad nutricional,
    "nutrients": [
        {{"name": "Calorías", "value": "valor", "unit": "kcal", "percentage": porcentaje_VD_o_null, "status": "good/warning/danger/normal"}},
        {{"name": "Grasas Totales", "value": "valor", "unit": "g", "percentage": porcentaje_VD_o_null, "status": "status"}},
        {{"name": "Grasas Saturadas", "value": "valor", "unit": "g", "percentage": porcentaje_VD_o_null, "status": "status"}},
        {{"name": "Carbohidratos", "value": "valor", "unit": "g", "percentage": porcentaje_VD_o_null, "status": "status"}},
        {{"name": "Azúcares", "value": "valor", "unit": "g", "percentage": porcentaje_VD_o_null, "status": "status"}},
        {{"name": "Fibra", "value": "valor", "unit": "g", "percentage": porcentaje_VD_o_null, "status": "status"}},
        {{"name": "Proteínas", "value": "valor", "unit": "g", "percentage": porcentaje_VD_o_null, "status": "status"}},
        {{"name": "Sodio", "value": "valor", "unit": "mg", "percentage": porcentaje_VD_o_null, "status": "status"}}
    ],
    "ingredients": ["ingrediente1", "ingrediente2", ...],
    "warnings": ["advertencia1", "advertencia2", ...],
    "recommendations": ["recomendación1", "recomendación2", ...]
}}

Criterios para status:
- "good": valor bajo/saludable (fibra alta, proteína alta, sodio bajo)
- "warning": valor moderado-alto (azúcar moderado, grasas saturadas moderadas)  
- "danger": valor muy alto/preocupante (azúcar muy alto, sodio muy alto)
- "normal": valor dentro de rangos normales

Criterios para health_score:
- 80-100: Producto muy saludable
- 60-79: Producto moderadamente saludable
- 40-59: Producto con aspectos a mejorar
- 0-39: Producto poco recomendable

{user_context}

Si no puedes leer la etiqueta claramente, haz tu mejor estimación basándote en lo visible.
IMPORTANTE: Responde SOLO con el JSON, sin texto adicional."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"nutriscan-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("gemini", "gemini-3-flash-preview")
        
        # Create image content
        image_content = ImageContent(image_base64=image_base64)
        
        user_message = UserMessage(
            text="Analiza esta etiqueta nutricional y extrae toda la información. Responde en JSON.",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        import json
        # Clean response - remove markdown code blocks if present
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        data = json.loads(response_text)
        
        # Build nutrients list
        nutrients = []
        for n in data.get("nutrients", []):
            nutrients.append(NutrientInfo(
                name=n.get("name", ""),
                value=str(n.get("value", "0")),
                unit=n.get("unit", ""),
                percentage=n.get("percentage"),
                status=n.get("status", "normal")
            ))
        
        # Generate personalized alerts if user profile exists
        personalized_alerts = []
        if user_profile:
            personalized_alerts = generate_personalized_alerts(
                user_profile,
                data.get("ingredients", []),
                nutrients
            )
        
        result = AnalysisResult(
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
        
        return result
        
    except Exception as e:
        logging.error(f"Gemini analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {str(e)}")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserCreate):
    """Register a new user"""
    # Check if email exists
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "name": data.name,
        "profile": (data.profile or UserProfile()).model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    # Create session
    token = generate_token()
    await db.sessions.insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return TokenResponse(
        token=token,
        user=UserResponse(
            id=user_id,
            email=user["email"],
            name=user["name"],
            profile=UserProfile(**user["profile"]),
            created_at=user["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    """Login user"""
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user or user["password_hash"] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Create new session
    token = generate_token()
    await db.sessions.insert_one({
        "token": token,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return TokenResponse(
        token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            profile=UserProfile(**user.get("profile", {})),
            created_at=user["created_at"]
        )
    )

@api_router.post("/auth/logout")
async def logout(user: dict = Depends(require_user), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user"""
    await db.sessions.delete_one({"token": credentials.credentials})
    return {"message": "Sesión cerrada"}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(require_user)):
    """Get current user"""
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        profile=UserProfile(**user.get("profile", {})),
        created_at=user["created_at"]
    )

@api_router.put("/auth/profile", response_model=UserResponse)
async def update_profile(data: UserUpdate, user: dict = Depends(require_user)):
    """Update user profile"""
    update_data = {}
    if data.name:
        update_data["name"] = data.name
    if data.profile:
        update_data["profile"] = data.profile.model_dump()
    
    if update_data:
        await db.users.update_one({"id": user["id"]}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    return UserResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        name=updated_user["name"],
        profile=UserProfile(**updated_user.get("profile", {})),
        created_at=updated_user["created_at"]
    )

# ==================== ANALYSIS ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "NutriScan AI API - Análisis de etiquetas nutricionales con IA"}

@api_router.post("/analyze", response_model=AnalysisResult)
async def analyze_label(request: AnalyzeRequest, user: Optional[dict] = Depends(get_current_user)):
    """Analyze a food label image using Gemini 3 Flash"""
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="Se requiere una imagen")
    
    # Get user profile if authenticated
    user_profile = None
    user_id = None
    if user:
        user_profile = UserProfile(**user.get("profile", {}))
        user_id = user["id"]
    
    # Analyze with Gemini
    result = await analyze_with_gemini(request.image_base64, user_profile)
    result.user_id = user_id
    
    # Store in database
    doc = result.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.scan_history.insert_one(doc)
    
    return result

@api_router.get("/history", response_model=List[AnalysisResult])
async def get_scan_history(user: dict = Depends(require_user)):
    """Get user's scan history"""
    history = await db.scan_history.find(
        {"user_id": user["id"]}, 
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    
    for item in history:
        if isinstance(item['timestamp'], str):
            item['timestamp'] = datetime.fromisoformat(item['timestamp'])
    
    return history

# ==================== CHAT ROUTES ====================

def get_personality_prompt(strictness_level: str) -> str:
    """Get AI personality based on strictness level"""
    personalities = {
        "relaxed": """Eres un nutricionista amigable y relajado. 
        - Sé comprensivo y no juzgues las elecciones alimentarias
        - Da consejos suaves y positivos
        - Si algo no es muy saludable, menciónalo con tacto
        - Usa un tono casual y cercano""",
        
        "normal": """Eres un nutricionista profesional y equilibrado.
        - Da información objetiva y clara
        - Señala tanto lo positivo como lo negativo
        - Ofrece alternativas cuando sea necesario
        - Mantén un tono profesional pero accesible""",
        
        "strict": """Eres un nutricionista estricto y directo.
        - Sé honesto sobre los aspectos negativos de los alimentos
        - Critica los ultraprocesados y azúcares añadidos
        - No suavices la verdad, el usuario quiere claridad
        - Da recomendaciones firmes para mejorar la dieta""",
        
        "very_strict": """Eres un nutricionista MUY EXIGENTE y sin filtros.
        - Sé brutalmente honesto sobre la comida basura y ultraprocesados
        - Usa sarcasmo cuando el producto sea claramente poco saludable
        - Compara los ingredientes dañinos con lo que realmente son (ej: "esto es básicamente azúcar disfrazada")
        - No tengas piedad con los productos llenos de aditivos
        - El usuario quiere la verdad cruda, dásela
        - Si algo es malo, dilo claramente: "esto es veneno procesado" o "tu cuerpo no necesita esta basura"
        - Pero también reconoce y celebra cuando algo es genuinamente saludable"""
    }
    return personalities.get(strictness_level, personalities["normal"])

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, user: Optional[dict] = Depends(get_current_user)):
    """Chat with AI about the analyzed product"""
    
    # Get analysis from database
    analysis = await db.scan_history.find_one({"id": request.analysis_id}, {"_id": 0})
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    
    # Get or create chat history for this analysis
    chat_doc = await db.chat_history.find_one({"analysis_id": request.analysis_id}, {"_id": 0})
    
    if not chat_doc:
        chat_doc = {
            "analysis_id": request.analysis_id,
            "user_id": user["id"] if user else None,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_history.insert_one(chat_doc)
    
    # Build user context
    user_context = ""
    strictness = "normal"
    if user:
        profile = user.get("profile", {})
        strictness = profile.get("strictness_level", "normal")
        
        if profile.get("weight"):
            user_context += f"\n- Peso: {profile['weight']} kg"
        if profile.get("height"):
            user_context += f"\n- Altura: {profile['height']} cm"
        if profile.get("sex"):
            sex_map = {"male": "Masculino", "female": "Femenino", "other": "Otro"}
            user_context += f"\n- Sexo: {sex_map.get(profile['sex'], profile['sex'])}"
        if profile.get("activity_level"):
            activity_map = {"sedentary": "Sedentario", "light": "Ligera", "moderate": "Moderada", "active": "Activa", "very_active": "Muy activa"}
            user_context += f"\n- Actividad física: {activity_map.get(profile['activity_level'], profile['activity_level'])}"
        if profile.get("goal"):
            goal_map = {"lose_weight": "Perder peso", "maintain": "Mantener peso", "gain_muscle": "Ganar músculo", "health": "Mejorar salud"}
            user_context += f"\n- Objetivo: {goal_map.get(profile['goal'], profile['goal'])}"
        if profile.get("allergies"):
            user_context += f"\n- Alergias: {', '.join(profile['allergies'])}"
        if profile.get("conditions"):
            user_context += f"\n- Condiciones de salud: {', '.join(profile['conditions'])}"
    
    # Build analysis context
    analysis_context = f"""
PRODUCTO ANALIZADO:
- Nombre: {analysis.get('product_name', 'Desconocido')}
- Marca: {analysis.get('brand', 'Desconocida')}
- Porción: {analysis.get('serving_size', 'No especificada')}
- Puntuación de salud: {analysis.get('health_score', 'N/A')}/100

INFORMACIÓN NUTRICIONAL:
"""
    for nutrient in analysis.get('nutrients', []):
        analysis_context += f"- {nutrient['name']}: {nutrient['value']} {nutrient['unit']}"
        if nutrient.get('percentage'):
            analysis_context += f" ({nutrient['percentage']}% VD)"
        analysis_context += f" - Estado: {nutrient.get('status', 'normal')}\n"
    
    if analysis.get('ingredients'):
        analysis_context += f"\nINGREDIENTES: {', '.join(analysis['ingredients'])}"
    
    if analysis.get('warnings'):
        analysis_context += f"\nADVERTENCIAS: {', '.join(analysis['warnings'])}"
    
    # Build conversation history
    conversation_history = ""
    for msg in chat_doc.get("messages", [])[-10:]:  # Last 10 messages for context
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        conversation_history += f"\n{role}: {msg['content']}"
    
    # Get personality based on strictness
    personality = get_personality_prompt(strictness)
    
    system_prompt = f"""{personality}

CONTEXTO DEL ANÁLISIS:
{analysis_context}

{"PERFIL DEL USUARIO:" + user_context if user_context else ""}

{"CONVERSACIÓN PREVIA:" + conversation_history if conversation_history else ""}

INSTRUCCIONES:
- Responde en ESPAÑOL
- Sé conciso pero informativo (2-4 frases máximo por respuesta)
- Basa tus respuestas en los datos del análisis y el perfil del usuario
- Si el usuario pregunta algo específico sobre un nutriente, dale datos concretos
- Adapta tu tono según el nivel de exigencia configurado
- Si hay una imagen adjunta, analízala en contexto con la pregunta"""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"nutriscan-chat-{request.analysis_id}",
            system_message=system_prompt
        ).with_model("gemini", "gemini-3-flash-preview")
        
        # Build message with optional image
        if request.image_base64:
            image_content = ImageContent(image_base64=request.image_base64)
            user_message = UserMessage(
                text=request.message,
                image_contents=[image_content]
            )
        else:
            user_message = UserMessage(text=request.message)
        
        response = await chat.send_message(user_message)
        
        # Save messages to history
        await db.chat_history.update_one(
            {"analysis_id": request.analysis_id},
            {"$push": {"messages": {
                "$each": [
                    {"role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc).isoformat()},
                    {"role": "assistant", "content": response, "timestamp": datetime.now(timezone.utc).isoformat()}
                ]
            }}}
        )
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el chat: {str(e)}")

@api_router.get("/chat/{analysis_id}")
async def get_chat_history(analysis_id: str, user: dict = Depends(require_user)):
    """Get chat history for an analysis"""
    chat_doc = await db.chat_history.find_one(
        {"analysis_id": analysis_id, "user_id": user["id"]}, 
        {"_id": 0}
    )
    
    if not chat_doc:
        return {"messages": []}
    
    return {"messages": chat_doc.get("messages", [])}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
