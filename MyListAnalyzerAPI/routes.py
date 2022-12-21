from MyListAnalyzerAPI.parse_user_anime_list import give_over_view, generate_report_for_recent_animes, parse_user_anime_list, fetch_recent_animes
from starlette.routing import Mount, Route


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

my_list_analyzer = Mount(path="/MLA", routes=[
    dynamic_table_routes, static_table_routes
])
