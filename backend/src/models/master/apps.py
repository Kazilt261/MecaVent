from typing import Optional
from sqlmodel import Field

from src.models.db_declarations import MasterMetadata

class Apps(MasterMetadata, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name_client: str = Field(index=True, unique=True)
    db_client: str = Field(default="default")
    redis_client: str = Field(default="default")

class Urls(MasterMetadata, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_app: int = Field(foreign_key="apps.id")
    urls: str = Field(default="")
    
class Access_app(MasterMetadata, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_app: int = Field(foreign_key="apps.id")
    access_app: str = Field(default="")