import typing
from dataclasses import dataclass
from enum import Enum

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


class DecodeEnum(Enum):
    @classmethod
    def give(cls, index):
        return cls[index].value


ep_range_bin = [
    12, 24, 100, 200, 500
]
# bin[i - 1] <= x < bin[i] implies that x is in bin [i]
# examples 12 is in second bin, 24 is also on second bin

bw_json_frame = "values"
date_unit = "ms"

rating = DecodeEnum("Rating", ("g", "pg", "pg_13", "r", "r+", "rx", "-"), start=0)
decode_rating = "All", "Children", "13+", "17+", "Mild Nudity", "Hentai", "Unknown"
media_type = DecodeEnum("Media Type", ("movie", "music", "ona", "ova", "special", "tv", "unknown"), start=0)
decode_media_type = "Movie", "Music", "ONA", "OVA", "Special", "TV", "Unknown"
list_status_enum = DecodeEnum("Status", ("completed", "watching", "dropped", "plan_to_watch", "on_hold"), start=0)
decode_list_status = "Completed", "Watching", "Dropped", "Planned", "On Hold"
