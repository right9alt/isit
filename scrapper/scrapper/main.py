import uvicorn, os, asyncpg
from fastapi import Request, FastAPI
from scrapper.models import ScraperParams
from scrapper import scrapper
from scrapper.utils import Context
from scrapper import query

app = FastAPI()

ctx = Context()

@app.on_event("startup")
async def startup_event():
  """Вызывается при запуске приложения."""
  ctx.db_handle = await query.connect()

@app.on_event("shutdown")
async def shutdown_event():
  await query.disconnect(ctx.db_handle)

@app.post("/start")
async def start(request: ScraperParams):
  ctx.set_logger_handler(os.getenv("SCRAPPER_LOG"))
  await scrapper.scrap(request.max_images, request.start_url, ctx)

def loader():
  """Launched with `poetry run start`"""
  uvicorn.run("scrapper.main:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")), reload=True)
