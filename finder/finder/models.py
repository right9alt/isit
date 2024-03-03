from pydantic import BaseModel

class ImageIdParams(BaseModel):
  image_id: int

class ClipParams(BaseModel):
  search_text: str