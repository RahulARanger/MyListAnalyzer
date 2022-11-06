import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from MyListAnalyzerAPI.modals import ProcessUserDetails
from MyListAnalyzerAPI.utils import DataDrip
from MyListAnalyzerAPI.user_details_report import report_gen as general_report

router = APIRouter(prefix="/user_details")


ROUTES = [general_report, False]


@router.post("/process/")
async def parse_user_details(request_details: ProcessUserDetails):
    is_raw = isinstance(request_details.data, list)
    drip = DataDrip.from_api(request_details.data, True) if is_raw else DataDrip.from_raw(request_details.data)

    try:
        content = {"meta": ROUTES[request_details.tab](drip)}

        if is_raw:
            content["drip"] = drip()

        return JSONResponse(
            content=content,
            status_code=200
        )

    except Exception as error:
        logging.exception("Failed to process User Details", exc_info=True)
        return JSONResponse(
            content={
                "failed": str(error)
            }, status_code=406
        )
