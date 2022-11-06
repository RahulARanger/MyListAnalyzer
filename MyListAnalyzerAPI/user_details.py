import logging
from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sanic_ext import validate
from sanic.exceptions import SanicException
from MyListAnalyzerAPI.modals import ProcessUserDetails
from MyListAnalyzerAPI.user_details_report import report_gen as general_report
from MyListAnalyzerAPI.utils import DataDrip

blue_print = Blueprint("report-generation-for-user-details", url_prefix="/user_details")

ROUTES = [general_report, False]


# @validate(json={})
# async def check_for_drip(request: Request):
#     ...


@blue_print.post("/process/")
@validate(json=ProcessUserDetails)
async def parse_user_details(_, body: ProcessUserDetails):
    is_raw = isinstance(body.data, list)
    try:
        drip = DataDrip.from_api(body.data, True) if is_raw else DataDrip.from_raw(body.data)

        content = {"meta": ROUTES[body.tab](drip)}

        if is_raw:
            content["drip"] = drip()

        return json(
            body=content,
            status=200
        )

    except Exception as error:
        raise SanicException(
            f"Failed to process User Details: {repr(error)}",
            status_code=406, quiet=False
        )
