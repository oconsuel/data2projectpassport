from pydantic import BaseModel
from typing import List, Optional  

class ProjectCreate(BaseModel):
    name: str

class ProjectPassport(BaseModel):
    summary_short: str
    summary_long: str
    tags: List[str]
    recommendations: Optional[str] = None

    class Config:
        orm_mode = True

class ProjectPassportSubfile(BaseModel):
    filename: str
    summary_short: str
    summary_long: str
    tags: List[str]
    recommendations: Optional[str] = None

    class Config:
        orm_mode = True
