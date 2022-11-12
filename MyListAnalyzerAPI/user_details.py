import logging
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
    tab_index = request.path_params["tab"]

    key_tests(tab_index)

    body = ProcessUserDetails(**await request.json())

    is_raw = isinstance(body.data, list)
    drip = DataDrip.from_api(body.data, True) if is_raw else DataDrip.from_raw(body.data)

    content = {"meta": ROUTES[tab_index](drip, body.timezone)}

    if is_raw:
        content["drip"] = drip()

    return JSONResponse(
        content=content
    )


def key_tests(tab_index):
    assert tab_index < len(ROUTES), "please request for the index 0 to %s" % (len(ROUTES) - 1,)
