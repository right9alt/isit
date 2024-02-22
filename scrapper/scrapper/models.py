
from pydantic import BaseModel

class ScraperParams(BaseModel):
  start_url: str
  max_images: int