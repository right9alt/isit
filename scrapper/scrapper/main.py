import uvicorn, os
from pydantic import BaseModel
from fastapi import Request, FastAPI
from dotenv import dotenv_values
from scrapper import scrapper

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

app = FastAPI()

class ScraperParams(BaseModel):
    start_url: str
    max_images: int

@app.post("/start")
async def start(request: Request, params: ScraperParams):
    body = await request.json()
    await scrapper.scrap(body['max_images'], body['start_url'])

def loader():
    """Launched with `poetry run start`"""
    uvicorn.run("scrapper.main:app", host=ENV["HOST"], port=int(ENV["PORT"]), reload=True)
