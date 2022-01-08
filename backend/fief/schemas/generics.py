from pydantic import UUID4, BaseModel


class UUIDSchema(BaseModel):
    id: UUID4

    class Config:
        orm_mode = True
