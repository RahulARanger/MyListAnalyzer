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
    tab: typing.Optional[int] = 0

