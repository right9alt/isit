import uvicorn, os
from fastapi import Request, FastAPI
from modificator import rembcg
from modificator import duplicates
from modificator import pyramid
from modificator.utils.utils import Context
from modificator.utils import database
from modificator.models import PyramidParams

app = FastAPI()

ctx = Context()

@app.on_event("startup")
async def startup_event():
  """Вызывается при запуске приложения."""
  ctx.db_handle = await database.connect()

@app.on_event("shutdown")
async def shutdown_event():
  await database.disconnect(ctx.db_handle)

@app.post("/rem_bg")
async def rem_bg():
  ctx.set_logger_handler(os.getenv("REMBCG_LOG"))
  await rembcg.rem_bg(ctx)

@app.post("/rem_dup")
async def rem_dup():
  ctx.set_logger_handler(os.getenv("DUPLICATES_LOG"))
  await duplicates.rem_dup(ctx)

@app.post("/pyramid")
async def pyramid_handler(request: PyramidParams):
  ctx.set_logger_handler(os.getenv("PYRAMID_LOG"))
  await pyramid.pyramid_start(request.first_image_id, request.second_image_id, ctx)

def loader():
  """Launched with `poetry run start`"""
  uvicorn.run("modificator.main:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")), reload=True)
