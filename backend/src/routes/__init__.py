from .admin.auth.auth import router as auth_admin_router
from .auth.auth import router as auth_router

routes = [auth_admin_router, auth_router]