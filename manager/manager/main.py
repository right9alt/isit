import uvicorn, os, asyncio
from fastapi import FastAPI
from manager.utils.models import ClipParams, ImageIdParams, PyramidParams, ScraperParams
from manager.request_manager import RequestManager

app = FastAPI()

@app.post("/scrap")
async def scrap(request: ScraperParams):
  json_data = {
    "start_url": request.start_url,
    "max_images": request.max_images
  }
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("SCRAP_URL_SCRAP"), json_data)
  return result

@app.post("/rem_bg")
async def rem_bg():

  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("MODIFICATOR_URL_REM_BG"), None)
  return result

@app.post("/rem_dup")
async def rem_dup():

  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("MODIFICATOR_URL_REM_DUP"), None)
  return result

@app.post("/pyramid")
async def pyramid(request: PyramidParams):
  json_data = {
    "first_image_id": request.first_image_id,
    "second_image_id": request.second_image_id
  }
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("MODIFICATOR_URL_PYRAMID"), json_data)
  return result

@app.post("/hsv")
async def hsv(request: ImageIdParams):
  json_data = {
    "image_id": request.image_id
  }
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("FINDER_URL_HSV"), json_data)
  return result

@app.post("/ciedge2000")
async def ciedge2000(request: ImageIdParams):
  json_data = {
    "image_id": request.image_id
  }
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("FINDER_URL_CIEDGE"), json_data)
  return result

@app.post("/photo")
async def photo(request: ImageIdParams):
  json_data = {
    "image_id": request.image_id
  }
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("FINDER_URL_PHOTO"), json_data)
  return result

@app.post("/classify")
async def classify(request: ImageIdParams):
  json_data = {
    "image_id": request.image_id
  }
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("FINDER_URL_CLASS"), json_data)
  return result

@app.post("/clip")
async def clip(request: ClipParams):
  json_data = {
    "search_text": request.search_text
  }
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, RequestManager.post, os.getenv("FINDER_URL_CLIP"), json_data)
  return result

def start():
  """Launched with `poetry run start`"""
  uvicorn.run("manager.main:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")), reload=True)