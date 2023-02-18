import json
import pathlib
import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse

dummy = pathlib.Path(__file__).parent / "DummyResp"


def file_to_json_resp(path):
    return JSONResponse(content=json.loads(path.read_text()))


def patched_request(*_):
    return file_to_json_resp(dummy / "fetchUserAnimeList.json")


def patched_request_process(*_):
    return file_to_json_resp(dummy / "userAnimeList.json")


def patched_overview(*_):
    return file_to_json_resp(dummy / "overView.json")


def patched_request_recently(*_):
    return file_to_json_resp(dummy / "fetchRecentAnimes.json")


def patched_validate_user(*_):
    return file_to_json_resp(dummy / "validateUser.json")


def patched_recent(*_):
    return file_to_json_resp(dummy / "recently.json")


origins = [
    "http://127.0.0.1:6969"
]

main_route = Mount("/MLA", routes=[
    Route("/dynamic/Overview", patched_overview, methods=["POST"]),
    Route("/fetchUserAnimeList", patched_request, methods=["GET"]),
    Route("/static/UserAnimeList", patched_request_process, methods=["POST"]),
    Route("/static/RecentAnimeList", patched_request_recently, methods=["POST"]),
    Route("/validateUser", patched_validate_user, methods=["GET"]),
    Route("/dynamic/Recently", patched_recent, methods=["POST"]),
])

app = Starlette(debug=True, routes=[main_route], middleware=[
    Middleware(
        CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=True
    )
])

if __name__ == "__main__":
    uvicorn.run("patchedServer:app", reload=True, port=6966, host="127.0.0.1", log_level="info")
