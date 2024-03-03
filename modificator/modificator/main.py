import uvicorn, os
from fastapi import Request, FastAPI
from dotenv import dotenv_values
from modificator import rembcg
from modificator import duplicates
from modificator import pyramid
from modificator.models import PyramidParams

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

app = FastAPI()

@app.post("/rem_bg")
async def start():
    await rembcg.rem_bg()

@app.post("/rem_dup")
async def rem_dup():
    await duplicates.rem_dup()

@app.post("/pyramid")
async def rem_dup(request: PyramidParams):
    await pyramid.pyramid(request.first_image_id, request.second_image_id)

def loader():
    """Launched with `poetry run start`"""
    uvicorn.run("modificator.main:app", host=ENV["HOST"], port=int(ENV["PORT"]), reload=True)
