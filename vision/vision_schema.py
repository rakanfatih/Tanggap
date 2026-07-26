from pydantic import BaseModel

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