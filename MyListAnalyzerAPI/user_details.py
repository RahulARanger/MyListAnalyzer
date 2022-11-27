import logging
from MyListAnalyzerAPI.modals import ProcessUserDetails
from MyListAnalyzerAPI.user_details_report import report_gen as general_report
from MyListAnalyzerAPI.utils import DataDrip
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response, PlainTextResponse
from starlette.requests import Request
import typing
import httpx


class HandleProcessUserDetails(BaseHTTPMiddleware):
    async def dispatch(
            self, request: Request, call_next: RequestResponseEndpoint
    ) -> typing.Union[JSONResponse, Response, PlainTextResponse]:

        logging.info("Requested to process User Details for: %s", request.url)

        try:
            response = await call_next(request)
            return response

        except Exception as error:
            logging.exception("Failed to process User Details for the %s", request.url, exc_info=True)

            # TODO:  Conduct some tests to provide the exact reason
            return PlainTextResponse(content=repr(error), status_code=406)


async def report_for_recent_animes(some_thing, timezone):
    print(some_thing, "was passed")
    return "tested"


ROUTES = {
    "Overview": general_report,
    "Recently": report_for_recent_animes
}


async def parse_user_details(request: Request):
    tab_index = request.path_params["tab"]

    assert tab_index in ROUTES, "Tab Index doesn't exist in ROUTES"
    body = ProcessUserDetails(**await request.json())

    is_raw = isinstance(body.data, list)
    is_drip = any((is_raw, isinstance(body.data, dict)))

    drip = DataDrip.from_api(
        body.data, True) if is_raw else DataDrip.from_raw(
        body.data) if is_drip else ""

    content = {"meta": await ROUTES[tab_index](drip, body.timezone)}

    if is_raw:
        content["drip"] = drip()

    return JSONResponse(
        content=content
    )
