from typing import Optional

from fastapi import APIRouter, Depends
from src.db.db import get_master_session
from src.models.master import Apps, Urls
from sqlmodel import select
from src.db.redis import redis_master

app_router = APIRouter(
    prefix="/app",
    tags=["app_data"]
)

@app_router.get("/tenant_id")
async def get_tenant_id(
    session_master=Depends(get_master_session),
    host_name: Optional[str] = None
):
    #filter the host_name from the request header
    if not host_name:
        return None

    # Get data from redis
    data_redis = redis_master.get(f"tenant_id:client_host={host_name}")
    if data_redis:
        data_redis = data_redis.decode("utf-8")
        json_data = eval(data_redis)  # Convert string back to dictionary
        return json_data

    # Get data from db
    query = select(Apps.id, Apps.name_client,Urls.urls).where(Apps.id == Urls.id_app).where(Urls.urls == host_name)
    get_tenant_data = session_master.exec(query).first()
    if not get_tenant_data:
        return None
    tenant_data = {
        "tenant_id": get_tenant_data[0],
        "name_client": get_tenant_data[1]
    }
    # Set data to redis
    redis_master.set(f"tenant_id:client_host={host_name}", str(tenant_data))

    return tenant_data