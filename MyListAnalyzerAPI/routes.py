from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from MyListAnalyzerAPI.fetch_sources import MALSession
from MyListAnalyzerAPI.modals import ValidateUser
from MyListAnalyzerAPI.parse_user_anime_list import give_over_view, generate_report_for_recent_animes, \
    parse_user_anime_list, fetch_recent_animes


async def validate_user(request: Request):
    user_name = ""
    try:
        user = ValidateUser(**await(request.json()))
        user.token = request.headers.get("token", "")
        user_name, reason = await MALSession().who_is_the_user(user.user_name, user.token)
    except Exception as error:
        reason = repr(error)

    failed = bool(reason)
    return JSONResponse(
        content=dict(passed=not failed, reason=reason, user_name=user_name),
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

validate_user_ep = Route("/validate_user", validate_user, methods=["POST"])

my_list_analyzer = Mount(path="/MLA", routes=[
    dynamic_table_routes, static_table_routes, validate_user_ep
])
