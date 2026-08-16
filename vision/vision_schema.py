from pydantic import BaseModel
from typing import Optional


class VisionOutput(BaseModel):
    flood_detected: bool
    confidence: float
    severity: str
    estimated_water_level: str
    estimated_water_cm: float
    water_percentage: float
    visible_objects: list[str]
    object_count: int
    image_quality: str
    possible_fake: bool
    reason: str
    vision_image_path: Optional[str] = None