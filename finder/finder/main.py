import uvicorn
from pydantic import BaseModel
from fastapi import Request, FastAPI
from dotenv import dotenv_values
from finder.models import ImageIdParams, ClipParams
from finder import hsv, ciedge2000, photo, clip, classifier


# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

app = FastAPI()

@app.post("/hsv")
async def start(request: ImageIdParams):
    similar_images = await hsv.hsv(request.image_id)
    similar_image_ids = [image[0] for image in similar_images]
    return {"similar_image_by_hsv_ids": similar_image_ids}

@app.post("/ciedge2000")
async def start(request: ImageIdParams):
    return {"similar_image_by_ciedge2000_ids": await ciedge2000.ciedge2000(request.image_id)}

@app.post("/photo")
async def start(request: ImageIdParams):
    return {"similar_image_by_ciedge2000_ids": await photo.find_by_photo(request.image_id)}

@app.post("/clip")
async def start(request: ClipParams):
    return {"images_ids_by_clip": await clip.clip_search(request.search_text)}

@app.post("/class")
async def start(request: ImageIdParams):
    return {"image_class:": await classifier.predict_class(request.image_id)}

def loader():
    """Launched with `poetry run start`"""
    uvicorn.run("finder.main:app", host=ENV["HOST"], port=int(ENV["PORT"]), reload=True)
