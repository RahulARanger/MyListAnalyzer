import typing
import re
import xml.etree.ElementTree as Tree
import pandas
import numpy
from datetime import datetime
from MyListAnalyzerAPI.modals import bw_json_frame
from pytz import timezone


def flat_me(bulge, safe):
    # converts [{'id': ..., 'name': ...}...] to ids and saves {"${id}": "${name}"}
    if not bulge or numpy.all(pandas.isna(bulge)):
        return []

    _safe = {str(_["id"]): _["name"].strip() for _ in bulge}
    safe.update(_safe)
    return tuple(_safe.keys())


class DataDrip:
    sep = "."

    def __init__(self, source, genres=None, studios=None):
        self.__source: pandas.DataFrame = source
        self.genres = genres if genres else {}
        self.studios = studios if studios else {}

        self.source.set_index(self.source[self["node", "id"]], inplace=True, drop=True)

    def get_stats(self):
        return {
            "num_items": self.source.shape[0],
            "num_episodes": self.source[self["list_status", "num_episodes_watched"]].sum(),
            "num_days": self.source[self["list_status", "spent"]].sum()
        }

    def purify(self):
        self.source[self["list_status", "spent"]] = \
            self.source[self["node", "average_episode_duration"]] * \
            self.source[self["list_status", "num_episodes_watched"]] / 3600

        self.genres = {}
        index = self["node", "genres"]
        self.source[index] = self.source[index].apply(lambda x: flat_me(x, self.genres))

        self.studios = {}
        index = self["node", "studios"]
        self.source[index] = self.source[index].apply(lambda x: flat_me(x, self.studios))

    @property
    def source(self):
        return self.__source

    @classmethod
    def from_api(cls, raw: list, fix=False):
        raw = DataDrip(
            pandas.json_normalize(raw, sep=DataDrip.sep)
        )  # its default but to note

        raw.source.dropna(
            subset=[
                raw["node", "id"]
            ], inplace=True
        )  # if any

        raw.source.set_index(raw["node", "id"])
        raw.purify() if fix else ...

        return raw

    @classmethod
    def from_raw(cls, raw: dict):
        return DataDrip(
            pandas.read_json(raw.get("data", ""), orient="columns"),
            raw.get("genres", None),
            raw.get("studios", None)
        )

    def __getitem__(self, key: typing.Union[str, typing.Sequence[str]]):
        _key = f"{self.sep}".join(key) if isinstance(key, tuple) else key
        return _key

    def __call__(self):
        return dict(
            data=self.source.to_json(orient="columns"),
            genres=self.genres,
            studios=self.studios
        )


class XMLParser:
    columns = ["id", "title", "status", "total", "up_until", "updated_at"]
    calculated_cols = ["difference", "not_completed", "re_watched"]

    def __init__(self, what_to_parse):
        self.node = Tree.fromstring(what_to_parse)

        self.desc_regex = re.compile(r"([\w ]+) - ([?\d]+) of ([?\d]+) episodes")
        self.id_regex = re.compile(r"https:\/\/myanimelist\.net\/anime\/(\d+)")

        # Fri, 08 Nov 2022 08:18:15 -0800
        self.stamp_format = "%a, %d %b %Y %H:%M:%S %z"

    def parse_desc(self, desc_node: Tree.Element):
        desc = desc_node.text

        parsed = re.search(self.desc_regex, desc)

        if not parsed:
            return False, False, False

        status, watched, total = parsed.groups()
        return status, numpy.nan if total == "?" else int(total), numpy.nan if watched == "?" else int(watched)

    def gen_id(self, link_node: Tree.Element):
        link = link_node.text
        parsed = re.search(self.id_regex, link)

        return False if not parsed else parsed.group(1)

    def pub_date_to_datetime(self, stamp, time_zone):
        return datetime.strptime(stamp, self.stamp_format).astimezone(timezone(time_zone))

    @classmethod
    def to_frame(cls, what_to_parse: str, time_zone: str):
        parser = XMLParser(what_to_parse)

        rows = []

        for item in parser.node.find("channel").iter("item"):
            title = item.find("title").text
            desc = parser.parse_desc(item.find("description"))
            anime_id = parser.gen_id(item.find("link"))
            time_stamp = parser.pub_date_to_datetime(item.find("pubDate").text, time_zone)

            row = (anime_id, title, *desc, time_stamp)

            if not all(row):
                raise AssertionError(f"failed to parse recent animes because of the record: {row}")

            rows.append(row)

        rows.reverse()

        frame = pandas.DataFrame(rows, columns=cls.columns)
        calc_cols = iter(cls.calculated_cols)
        frame[next(calc_cols)] = frame[["id", "up_until"]].groupby("id").up_until.diff()

        frame[next(calc_cols)] = frame.difference.isna()
        frame.difference = frame.difference.fillna(1)

        frame[next(calc_cols)] = frame.difference < 0
        frame.difference = frame.difference.abs()

        return frame

    @classmethod
    def from_raw(cls, raw, time_zone) -> pandas.DataFrame:
        frame = pandas.read_json(raw, orient=bw_json_frame)
        frame.columns = cls.columns + cls.calculated_cols
        frame.updated_at = pandas.to_datetime(frame.updated_at, utc=True, unit="ms").dt.tz_convert(time_zone)
        return frame
