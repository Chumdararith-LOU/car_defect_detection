from typing import List, Optional

from pydantic import BaseModel


class ChampionModel(BaseModel):
    stage: str
    name: str
    path: str
    available: bool
    size_mb: Optional[float] = None


class ModelsList(BaseModel):
    models: List[ChampionModel]
