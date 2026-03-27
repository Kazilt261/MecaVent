from typing import Optional, Self

from pydantic import BaseModel

class InterfaceCheck(BaseModel):
    
    @classmethod
    def interface(cls, obj: dict) -> Optional[Self]:
        try:
            return cls.model_validate(obj)
        except Exception:
            return None