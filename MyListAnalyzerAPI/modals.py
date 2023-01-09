import typing
from dataclasses import dataclass

default_time_zone = "Asia/Tokyo"


@dataclass
class ProcessUserDetails:
    user_name: str
    timezone: typing.Optional[str] = default_time_zone
    data: typing.Optional[typing.Union[typing.List, typing.Dict]] = None


@dataclass
class ForUserAnimeList:
    user_name: str
    url: typing.Optional[str] = None


ep_range_bin = [
    12, 24, 100, 200, 500
]
# bin[i - 1] <= x < bin[i] implies that x is in bin [i]
# examples 12 is in second bin, 24 is also on second bin

bw_json_frame = "values"
date_unit = "ms"


rating = {
    'g': "All Ages",
    "pg": "Children",
    "pg_13": "Teens 13 or Older",
    "r": "17+ (violence & profanity)",
    "r+": "Mild Nudity",
    "rx": "Hentai"
}
