import logging
from MyListAnalyzerAPI.modals import ProcessUserDetails
from MyListAnalyzerAPI.user_anime_list_report import report_gen as general_report, process_recent_animes_by_episodes
from MyListAnalyzerAPI.utils import DataDrip, bw_json_frame
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.requests import Request
import typing
import httpx
from MyListAnalyzerAPI.utils import XMLParser

ROUTES = dict(Overview=general_report, Recently=process_recent_animes_by_episodes)


def understand_user_anime_list(raw: typing.Union[typing.List, typing.Dict], tz: str):
    return DataDrip.from_api(raw, tz, True) if isinstance(raw, list) else DataDrip.from_raw(raw)


async def _fetch_recent_animes(user_name, time_zone):
    # max 6 seconds
    async with httpx.AsyncClient(timeout=6) as client:
        logging.info("Fetching the Recent anime list of user: %s", user_name)
        raw_xml = await client.get(f'https://myanimelist.net/rss.php?type=rwe&u={user_name}')
        return XMLParser.to_frame(raw_xml.text, time_zone)


async def parse_user_anime_list(request: Request):
    details = ProcessUserDetails(**await request.json())
    try:
        return JSONResponse(
            content=dict(user_anime_list=understand_user_anime_list(details.data, details.timezone)())
        )
    except Exception as error:
        logging.exception("Failed to parse User Anime List", exc_info=True)
        return PlainTextResponse(
            f"Failed to parse User Anime List, Make sure the format sent is a valid one. Error: {repr(error)}",
            status_code=406
        )


async def fetch_recent_animes(request: Request):
    details = ProcessUserDetails(**await request.json())

    try:
        return JSONResponse(
            content=dict(
                recent_animes=(
                    await _fetch_recent_animes(details.user_name, details.timezone)
                ).to_json(orient=bw_json_frame, date_unit="ms"))
        )
    except Exception as error:
        logging.exception("Failed to fetch Recent Animes", exc_info=True)
        return PlainTextResponse(
            f"Failed to fetch and Parse Recent animes, Please refer to this error: {repr(error)}",
            status_code=406
        )


async def give_over_view(request: Request):
    try:
        raw = ProcessUserDetails(**await request.json())
        drip = understand_user_anime_list(raw.data, raw.timezone)
        content = await general_report(raw.timezone, drip, raw.nsfw)
        return JSONResponse(
            content=content
        )
    except Exception as error:
        logging.exception("Failed to generate overview report", exc_info=True)
        return PlainTextResponse(
            status_code=406,
            content=f"Failed to process user anime list for generating Report for overview, Please refer to this "
                    f"error: {repr(error)}"
        )


async def generate_report_for_recent_animes(request: Request):
    fetched = False
    try:
        anime_list = ProcessUserDetails(**await request.json())
        if not anime_list.data:
            fetched = True
            anime_list.data = await _fetch_recent_animes(anime_list.user_name, anime_list.timezone)
        else:
            anime_list.data = XMLParser.from_raw(anime_list.data, anime_list.timezone)

        assert anime_list.data is not False, "User has empty `Recent Anime List by Episodes.`"
        content = await process_recent_animes_by_episodes(anime_list.data, anime_list.timezone)

        if fetched:
            content["recent_animes"] = anime_list.data.to_json(orient=bw_json_frame, date_unit="ms")

    except Exception as error:
        logging.exception("Failed to fetch the recent animes, please refer to the following error", exc_info=True)
        return PlainTextResponse(
            content=(
                        "Failed to fetch recent animes" if fetched else
                        "Failed to generate report based on the recent animes received"
                    ) + f", Please refer to the error: {repr(error)}.",
            status_code=406
        )

    return JSONResponse(
        content=content
    )
