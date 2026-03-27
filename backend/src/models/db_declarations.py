from sqlalchemy.orm import declarative_base
from sqlmodel import SQLModel

# Creamos metadatos independientes
class MasterMetadata(SQLModel): 
    metadata = declarative_base().metadata

class AppMetadata(SQLModel): 
    metadata = declarative_base().metadata