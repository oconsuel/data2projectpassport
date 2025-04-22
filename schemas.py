from pydantic import BaseModel
from typing import List

class ProjectCreate(BaseModel):
    name: str

class ProjectPassport(BaseModel):
    summary_short: str
    summary_long: str
    tags: List[str]

    class Config:
        orm_mode = True
