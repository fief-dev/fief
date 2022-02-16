from datetime import datetime
from typing import Generic, List, TypeVar

from pydantic import UUID4, BaseModel

PM = TypeVar("PM", bound=BaseModel)


class UUIDSchema(BaseModel):
    id: UUID4

    class Config:
        orm_mode = True


class CreatedUpdatedAt(BaseModel):
    created_at: datetime
    updated_at: datetime


class PaginatedResults(Generic[PM], BaseModel):
    count: int
    results: List[PM]
