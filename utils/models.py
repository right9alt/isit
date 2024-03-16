from pydantic import BaseModel

class ScraperParams(BaseModel):
  start_url: str
  max_images: int

class PyramidParams(BaseModel):
  first_image_id: int
  second_image_id: int

class ImageIdParams(BaseModel):
  image_id: int

class ClipParams(BaseModel):
  search_text: str