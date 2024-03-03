from pydantic import BaseModel

class PyramidParams(BaseModel):
  first_image_id: int
  second_image_id: int