
from src.utils.types_utils import InterfaceCheck

class UserData(InterfaceCheck):
    id: int
    username: str
    email: str|None
    hashed_password: str