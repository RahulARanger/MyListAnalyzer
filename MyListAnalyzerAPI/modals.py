import typing
from pydantic import BaseModel


class ProcessUserDetails(BaseModel):
    data: typing.Union[typing.List, typing.Dict]
    tab: typing.Optional[int] = 0
