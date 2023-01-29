import json
import pathlib
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from MyListAnalyzerAPI.parse_user_anime_list import give_over_view, generate_report_for_recent_animes, \
    parse_user_anime_list, fetch_recent_animes


def from_json_to_json_resp(test_data):
    with (pathlib.Path(__file__).parent / "Test Data" / test_data).open() as read:
        return JSONResponse(content=json.load(read), status_code=200)


async def validate_user(request: Request):
    return from_json_to_json_resp("validateUser.psd")


async def fetch_user_anime_list(request: Request):
    return from_json_to_json_resp("fetchUserAnimeList.psd")


dynamic_table_routes = Mount(path="/dynamic", routes=[
    Route("/Overview", give_over_view, methods=["POST"]),
    Route("/Recently", generate_report_for_recent_animes, methods=["POST"]),
])

static_table_routes = Mount(
    path="/static", routes=[
        Route("/UserAnimeList", parse_user_anime_list, methods=["POST"]),
        Route("/RecentAnimeList", fetch_recent_animes, methods=["POST"]),
    ]
)

validate_user_ep = Route("/validateUser", validate_user, methods=["GET"])
fetch_user_anime_list_route = Route("/fetchUserAnimeList", fetch_user_anime_list, methods=["GET"])

my_list_analyzer = Mount(path="/MLA", routes=[
    dynamic_table_routes, static_table_routes, validate_user_ep, fetch_user_anime_list_route
])
