import logging
from MyListAnalyzerAPI.modals import ProcessUserDetails, bw_json_frame
from MyListAnalyzerAPI.user_anime_list_report import report_gen as general_report, process_recent_animes_by_episodes
from MyListAnalyzerAPI.utils import DataDrip
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.requests import Request
import pandas
import typing
import httpx
from MyListAnalyzerAPI.parser import XMLParser

ROUTES = dict(Overview=general_report, Recently=process_recent_animes_by_episodes)


async def parse_user_anime_list(request: Request):
    tab_name = request.path_params["tab"]
    error_code = 406

    if tab_name not in ROUTES:
        return PlainTextResponse(
            f"Invalid Argument, Expected values from any one of the {', '.join(ROUTES.keys())}",
            status_code=error_code
        )

    try:
        failed, response = await _parse_user_anime_list(ProcessUserDetails(**await request.json()), tab_name)
    except Exception as error:
        failed = True
        response = f"Failed because of {repr(error)}"
        logging.exception(response, exc_info=True)

    return JSONResponse(
        content=response, status_code=200
    ) if not failed else PlainTextResponse(
        content=response,
        status_code=error_code
    )


async def _parse_user_anime_list(anime_list: ProcessUserDetails, tab_name):
    user_anime_list = anime_list.data.get("user_anime_list", "")
    recent_animes = anime_list.data.get("recent_animes", "")

    if not recent_animes:
        _frame, errors = await _fetch_recent_animes(anime_list.user_name, anime_list.timezone)
        assert not errors, f"Failed to fetch recent animes: %s" % (", ".join(errors), )
    else:
        _frame: pandas.DataFrame = XMLParser.from_raw(
            recent_animes, anime_list.timezone) if anime_list.need_to_parse_recent else ""

    is_raw = isinstance(user_anime_list, list)
    is_drip = any((is_raw, isinstance(user_anime_list, dict)))

    drip = DataDrip.from_api(
        user_anime_list, True) if is_raw else DataDrip.from_raw(user_anime_list) if is_drip else ""

    content = dict(
        dripped=await ROUTES[tab_name](
            anime_list.user_name,
            anime_list.timezone,
            drip,
            _frame
        )
    )

    content["drip"] = drip() if is_raw else ""
    content["recent_animes"] = _frame.to_json(orient=bw_json_frame, date_unit="ms") if not (
            recent_animes or isinstance(_frame, str)) else ""
    return False, content


async def _fetch_recent_animes(user_name, time_zone):
    # max 6 seconds
    async with httpx.AsyncClient(timeout=6) as client:
        logging.info("Fetching the Recent anime list of user: %s", user_name)
        raw_xml = await client.get(f'https://myanimelist.net/rss.php?type=rwe&u={user_name}')
        return XMLParser.to_frame(raw_xml.text, time_zone)

# TODO:

"""
we can 2 data store for individual tabs
one for rendering the results in dashboard
other for sharing the results with the other tabs
"""