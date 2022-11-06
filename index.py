from fastapi import FastAPI
from MyListAnalyzerAPI.routes import application_router
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(description="Hey There")

origins = [
    "http://127.0.0.1:6969"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(application_router)


if __name__ == "__main__":
    uvicorn.run("index:app", port=6966, log_level="info", reload=True)

