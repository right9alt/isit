import uvicorn, os
from pydantic import BaseModel
from fastapi import Request, FastAPI
from finder.utils.models import ImageIdParams, ClipParams, PhotoFinderParams
from finder import hsv, ciedge2000, photo, clip, classifier, model_loader
from finder.utils.utils import Context
from finder.utils import database

app = FastAPI()

ctx = Context()

@app.on_event("startup")
async def startup_event():
  """Вызывается при запуске приложения."""
  ctx.db_handle = await database.connect()
  ctx.set_logger_handler(os.getenv("FINDER_LOG"))
  ctx.classify_model = model_loader.load_classify_model(os.getenv("MODEL_PATH"))
  ctx.photo_model = model_loader.load_photo_model()
  ctx.clip_model = model_loader.load_clip_model()

@app.on_event("shutdown")
async def shutdown_event():
  await database.disconnect(ctx.db_handle)

@app.post("/hsv")
async def start(request: ImageIdParams):
    similar_images = await hsv.hsv(request.image_id, ctx)
    similar_image_ids = [image[0] for image in similar_images]
    return {"similar_image_by_hsv_ids": similar_image_ids}

@app.post("/ciedge2000")
async def start(request: ImageIdParams):
    return {"similar_image_by_ciedge2000_ids": await ciedge2000.ciedge2000(request.image_id, ctx)}

@app.post("/photo")
async def start(request: PhotoFinderParams):
    return {"similar_image_by_promt_ids": await photo.find_by_photo(request.image_id, ctx, request.n_neighbors)}

@app.post("/clip")
async def start(request: ClipParams):
    return {"images_ids_by_clip": await clip.clip_search(request.search_text, ctx)}

@app.post("/classify")
async def classify(request: ImageIdParams):
    return {"image_class:": await classifier.predict_class(request.image_id, ctx)}

def loader():
    """Launched with `poetry run start`"""
    uvicorn.run("finder.main:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")), reload=True)
