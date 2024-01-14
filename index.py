from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from MyListAnalyzerAPI.routes import my_list_analyzer
import uvicorn
import logging
from dotenv import load_dotenv
import os

load_dotenv()
assert os.getenv("MAL_CLIENT_ID"), "We need client id for MAL"

logging.basicConfig(level=logging.INFO)


async def greet(_):
    return PlainTextResponse(
        content="Hello There"
    )


main_route = Route("/", greet)
origins = [
    "http://127.0.0.1:6969"
]

app = Starlette(debug=True, routes=[main_route, my_list_analyzer], middleware=[
    Middleware(
        CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=True
    )
])

if __name__ == "__main__":
    uvicorn.run("index:app", reload=True, port=6966, host="127.0.0.1", log_level="info")
