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


class ENumber:
    def __init__(self, encoder, decoder: typing.Sequence[typing.Union[str, int]]):
        """

        :param encoder: Encodes the String to a Number so the data send to the UI is lightweight
        :param decoder: decodes the Number to string. so user can understand
        """
        self.encoder = encoder
        self.decoder = decoder

    def give(self, index):
        return self.decoder[self.take(index)]

    def take(self, index):
        return getattr(self.encoder, index).value


rating = ENumber(
    Enum("Rating", ("g", "pg", "pg_13", "r", "r+", "rx", "-"), start=0),
    ("All", "Children", "13+", "17+", "Mild Nudity", "Hentai", "Unknown")
)

media_type = ENumber(
    Enum("Media Type", ("movie", "music", "ona", "ova", "special", "tv", "unknown", "tv_special"), start=0),
    ("Movie", "Music", "ONA", "OVA", "Special", "TV", "Unknown", "TV Special")
)

list_status_enum = ENumber(
    Enum("Status", ("completed", "watching", "dropped", "plan_to_watch", "on_hold"), start=0),
    ("Completed", "Watching", "Dropped", "Planned", "On Hold")
)
