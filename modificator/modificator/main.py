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
  ctx.set_logger_handler(os.getenv("MODIFICATOR_LOG"))


@app.on_event("shutdown")
async def shutdown_event():
  await database.disconnect(ctx.db_handle)

@app.post("/rem_bg")
async def rem_bg():
  await rembcg.rem_background(ctx)

@app.post("/rem_dup")
async def rem_dup():
  await duplicates.rem_duplicates(ctx)

@app.post("/pyramid")
async def pyramid_handler(request: PyramidParams):
  await pyramid.pyramid_start(request.first_image_id, request.second_image_id, ctx)

def loader():
  """Launched with `poetry run start`"""
  uvicorn.run("modificator.main:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")), reload=True)
