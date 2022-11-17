import typing
from dataclasses import dataclass
studios_or_genres = typing.List[typing.Dict[str, typing.Union[int, str]]]
list_status_or_broadcast_or_picture = typing.Dict[str, str]
season = typing.Dict[str, typing.Union[int, str]]

node_details_and_list_status = typing.Dict[
    str,
    typing.Dict[str, typing.Union[
        int, str, float, studios_or_genres, season, list_status_or_broadcast_or_picture
    ]]
]


@dataclass
class ProcessUserDetails:
    data: typing.List[
        node_details_and_list_status
    ]
    timezone: typing.Optional[str] = "Asia/Tokyo"


ep_range_bin = [
    12, 24, 100, 200, 500
]
# bin[i - 1] <= x < bin[i] implies that x is in bin [i]
# examples 12 is in second bin, 24 is also on second bin
