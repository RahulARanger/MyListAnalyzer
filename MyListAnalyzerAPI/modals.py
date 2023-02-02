import typing
from dataclasses import dataclass

default_time_zone = "Asia/Tokyo"


@dataclass
class ProcessUserDetails:
    user_name: str
    timezone: typing.Optional[str] = default_time_zone
    data: typing.Optional[typing.Union[typing.List, typing.Dict]] = None
    nsfw: typing.Optional[bool] = False


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
    'g': 0,
    "pg": 1,
    "pg_13": 2,
    "r": 3,
    "r+": 4,
    "rx": 5,
    "-": 6
}

decode_rating = ["All", "Children", "13+", "17+", "Mild Nudity", "Hentai", "Unknown"]
media_type = {"movie": 0, "music": 1, "ona": 2, "ova": 3, "special": 4, "tv": 5, "unknown": 6}
decode_media_type = ["Movie", "Music", "ONA", "OVA", "Special", "TV", "Unknown"]
