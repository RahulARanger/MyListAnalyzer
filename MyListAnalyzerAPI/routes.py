from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from MyListAnalyzerAPI.fetch_sources import MALSession
from MyListAnalyzerAPI.modals import ForUserAnimeList
from MyListAnalyzerAPI.parse_user_anime_list import give_over_view, generate_report_for_recent_animes, \
    parse_user_anime_list, fetch_recent_animes


async def validate_user(request: Request):
    user_name = "@me"
    try:
        user_name = request.query_params.get("user_name", "")
        token = request.headers.get("token", "")
        user_name, reason = await MALSession().who_is_the_user(user_name, token)
    except Exception as error:
        reason = repr(error)

    failed = bool(reason)
    return JSONResponse(
        content=dict(passed=not failed, reason=reason, user_name=user_name),
        status_code=406 if failed else 200
    )


async def fetch_user_anime_list(request: Request):
    token = request.headers.get("token", "")
    user_name = "@me"
    reason = False
    results = dict(user_name=user_name)

    try:
        temp = ForUserAnimeList(**request.query_params)
        user_name = temp.user_name if temp.user_name else user_name
        results.update(user_name=user_name)
        results.update(await MALSession().fetch_list(user_name, token, temp.url))
    except Exception as error:
        reason = repr(error)

    failed = bool(reason)

    return JSONResponse(
        content=dict(passed=not failed, reason=reason, **results),
        status_code=406 if failed else 200
    )


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
