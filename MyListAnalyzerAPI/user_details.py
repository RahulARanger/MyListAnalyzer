import logging
import pprint

from MyListAnalyzerAPI.modals import ProcessUserDetails
from MyListAnalyzerAPI.user_details_report import report_gen as general_report
from MyListAnalyzerAPI.utils import DataDrip
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response, PlainTextResponse
from starlette.requests import Request
import typing


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


ROUTES = [general_report, False]


async def parse_user_details(request: Request):
    body = ProcessUserDetails(**await request.json())

    is_raw = isinstance(body.data, list)
    drip = DataDrip.from_api(body.data, True) if is_raw else DataDrip.from_raw(body.data)

    content = {"meta": ROUTES[body.tab](drip)}

    if is_raw:
        content["drip"] = drip()

    pprint.pprint(content, indent=4)

    return JSONResponse(
        content=content
    )
