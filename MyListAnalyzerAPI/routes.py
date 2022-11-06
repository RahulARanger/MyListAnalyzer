from fastapi import APIRouter
from MyListAnalyzerAPI.user_details import router as user_router


application_router = APIRouter(prefix="/MLA")
application_router.include_router(user_router)

