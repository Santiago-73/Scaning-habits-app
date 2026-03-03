from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'nutriscan_db')]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class NutrientInfo(BaseModel):
    name: str
    value: str
    unit: str
    percentage: Optional[int] = None
    status: str = "normal"  # good, warning, danger

class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    brand: str
    serving_size: str
    health_score: int
    nutrients: List[NutrientInfo]
    warnings: List[str]
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnalyzeRequest(BaseModel):
    image_base64: Optional[str] = None

# Simulated analysis result for demo
def get_simulated_result() -> AnalysisResult:
    return AnalysisResult(
        product_name="Galletas Integrales de Avena",
        brand="NutriBio",
        serving_size="30g (3 galletas)",
        health_score=72,
        nutrients=[
            NutrientInfo(name="Calorías", value="142", unit="kcal", percentage=7, status="normal"),
            NutrientInfo(name="Grasas Totales", value="6.2", unit="g", percentage=9, status="normal"),
            NutrientInfo(name="Grasas Saturadas", value="2.1", unit="g", percentage=10, status="warning"),
            NutrientInfo(name="Carbohidratos", value="19", unit="g", percentage=7, status="normal"),
            NutrientInfo(name="Azúcares", value="7.5", unit="g", percentage=8, status="warning"),
            NutrientInfo(name="Fibra", value="2.8", unit="g", percentage=10, status="good"),
            NutrientInfo(name="Proteínas", value="2.4", unit="g", percentage=5, status="normal"),
            NutrientInfo(name="Sodio", value="95", unit="mg", percentage=4, status="good"),
        ],
        warnings=[
            "Contiene gluten",
            "Puede contener trazas de frutos secos",
            "Azúcar añadido moderado"
        ],
        recommendations=[
            "Buena fuente de fibra para la digestión",
            "Ideal como snack entre comidas",
            "Limitar a 1-2 porciones diarias"
        ]
    )

# Routes
@api_router.get("/")
async def root():
    return {"message": "NutriScan AI API - Análisis de etiquetas nutricionales"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

@api_router.post("/analyze", response_model=AnalysisResult)
async def analyze_label(request: AnalyzeRequest):
    """
    Analyzes a food label image and returns nutritional information.
    Currently returns simulated data. Ready for Gemini 3 Flash integration.
    """
    # Simulate processing delay
    import asyncio
    await asyncio.sleep(2)
    
    # Return simulated result
    result = get_simulated_result()
    
    # Store in database
    doc = result.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.scan_history.insert_one(doc)
    
    return result

@api_router.get("/history", response_model=List[AnalysisResult])
async def get_scan_history():
    """Get history of scanned labels"""
    history = await db.scan_history.find({}, {"_id": 0}).to_list(50)
    
    for item in history:
        if isinstance(item['timestamp'], str):
            item['timestamp'] = datetime.fromisoformat(item['timestamp'])
    
    return history

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
