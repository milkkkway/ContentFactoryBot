from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# !!! ПРЕДПОЛАГАЕМЫЙ ИМПОРТ: проверьте путь к вашему файлу
import api.YouTubeApi

app = FastAPI(title="My API", version="1.0.0")

# --- Настройка CORS ---
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.0.10:3000",
    "http://localhost:3000",
    "http://localhost:3000/calc"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


# --- Модель Pydantic для данных запроса ---
# (Обратите внимание: поля должны совпадать с ключами в вашем React-коде!)
class CalcReqModel(BaseModel):
    keyword: str  # 👈 ИСПРАВЛЕНО: должно быть 'keyword'
    region: str
    numPosts: int  # 👈 ИСПРАВЛЕНО: должно быть 'numPosts'
    minSubs: int  # 👈 ИСПРАВЛЕНО: должно быть 'minSubs'
    minVids: int  # 👈 ИСПРАВЛЕНО: должно быть 'minVids'


@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI!"}


# --- ИСПРАВЛЕННЫЙ РОУТ /calc ---
@app.post("/calc")
async def calculate_stat_youtube(model: CalcReqModel):
    return api.YouTubeApi.main(
        model.keyword,
        model.region,
        model.numPosts,
        model.minSubs,
        model.minVids
    )
@app.post("/calc_vk")
async def calculate_stat_vk(model: CalcReqModel):
    return api.VkApi.main(
        model.keyword,
        model.region,
        model.numPosts,
        model.minSubs,
        model.minVids
    )