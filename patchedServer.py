import json
import pathlib
import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, Mount

dummy = pathlib.Path(__file__).parent / "DummyResp"


def patched_request():
    return json.loads((dummy / "fetchUserAnimeList.json").read_text())


def patched_request_process():
    return json.loads((dummy / "userAnimeList.json").read_text())


def patched_overview():
    return json.loads((dummy / "overView.json").read_text())


def patched_request_recently():
    return json.loads((dummy / "recently.json").read_text())


def patched_validate_user():
    return json.loads((dummy / "validateUser.json").read_text())


origins = [
    "http://127.0.0.1:6969"
]

main_route = Mount("/MLA", routes=[
    Route("/Overview", patched_overview),
    Route("/fetchUserAnimeList", patched_request, methods=["GET"]),
    Route("/UserAnimeList", patched_request_process, methods=["POST"]),
    Route("/RecentAnimeList", patched_request_recently, methods=["POST"]),
    Route("/validateUser", patched_validate_user, methods=["GET"])
])

app = Starlette(debug=True, routes=[main_route], middleware=[
    Middleware(
        CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=True
    )
])

if __name__ == "__main__":
    uvicorn.run("index:app", reload=True, port=6966, host="127.0.0.1", log_level="info")
