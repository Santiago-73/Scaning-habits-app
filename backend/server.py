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
            image_contents=[image_content]
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
