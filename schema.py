from typing import List, Dict, Optional, Literal, Union, Annotated
from pydantic import BaseModel, Field

class ResourceConfig(BaseModel):
    bioreactor_volume: float = Field(..., description="Volume of the bioreactor in Liters")
    chromatography_skids: int = Field(..., description="Number of available chromatography skids")

class StepConfig(BaseModel):
    type: str
    name: str
    duration_hours: Optional[float] = None
    consumables: Dict[str, float] = Field(default_factory=dict)
    input_batch: Optional[str] = None

class FermentationConfig(StepConfig):
    type: Literal["Fermentation"]
    contamination_risk: float = Field(0.0, ge=0.0, le=1.0)
    growth_rate: float = Field(..., description="Growth rate in g/L per run")

class ChromatographyConfig(StepConfig):
    type: Literal["Chromatography"]
    cycle_time_hours: float
    cycles: int
    yield_step: float = Field(..., ge=0.0, le=1.0)

class MediaPrepConfig(StepConfig):
    type: Literal["MediaPrep"]

StepUnion = Annotated[Union[FermentationConfig, ChromatographyConfig, MediaPrepConfig], Field(discriminator='type')]

class RecipeConfig(BaseModel):
    resources: ResourceConfig
    steps: List[StepUnion]
