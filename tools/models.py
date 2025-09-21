from pydantic import BaseModel, Field
from typing import Optional

class Sismo(BaseModel):
    id: str
    timestamp: str
    lat: float
    lon: float
    mag: Optional[float] = Field(default=None)
