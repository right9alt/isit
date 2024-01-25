import uvicorn, os
from fastapi import FastAPI
from dotenv import dotenv_values

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

def start():
    """Launched with `poetry run start`"""
    uvicorn.run("isit_svc.main:app", host=ENV["HOST"], port=int(ENV["PORT"]), reload=True)
