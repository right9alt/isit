import uvicorn, os
from pydantic import BaseModel
from fastapi import Request, FastAPI
from dotenv import dotenv_values
from scrapper.models import ScraperParams
from scrapper import scrapper

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

app = FastAPI()

@app.post("/start")
async def start(request: ScraperParams):
    await scrapper.scrap(request.max_images, request.start_url)

def loader():
    """Launched with `poetry run start`"""
    uvicorn.run("scrapper.main:app", host=ENV["HOST"], port=int(ENV["PORT"]), reload=True)
