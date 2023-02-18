import logging
import re
import typing
import xml.etree.ElementTree as Tree
from datetime import datetime
import numpy
import pandas
from pytz import timezone
from MyListAnalyzerAPI.modals import bw_json_frame, default_time_zone


def flat_me(bulge, safe):
    # converts [{'id': ..., 'name': ...}...] to ids and saves {"${id}": "${name}"}
    if not bulge or numpy.all(pandas.isna(bulge)):
        return []

    # while storing in the storage, it is auto converted to string so
    _safe = {str(_["id"]): _["name"].strip() for _ in bulge}

    safe.update(_safe)
    return tuple(_safe.keys())


class DataDrip:
    sep = "."
    orient = "split"
    unit = 'ms'

    def __init__(self, source, genres=None, studios=None):
        self.__source: pandas.DataFrame = source
        self.genres = genres if genres else {}
        self.studios = studios if studios else {}

        self.source.set_index(self.source[self.node("id")], inplace=True, drop=True)

    def get_stats(self):
        return {
            "num_items": self.source.shape[0],
            "num_episodes": self.source[self.list_status("num_episodes_watched")].sum(),
            "num_days": self.source[self.list_status("spent")].sum()
        }

    @property
    def source(self):
        return self.__source

    @classmethod
    def from_api(cls, raw: list, tz: str = None, fix=False):
        raw = DataDrip(
            pandas.json_normalize(raw, sep=DataDrip.sep)
        )  # its default but to note

        raw.source.dropna(
            subset=[
                raw.node("id")
            ], inplace=True
        )  # if any

        # pandas.to_datetime(raw.source.list_status("updated_at"), utc=True, unit="ms").dt.tz_convert(time_zone)

        raw.source.set_index(raw.node("id"))
        raw.purify(timezone(tz) if tz else default_time_zone) if fix else ...

        return raw

    @classmethod
    def from_raw(cls, raw: dict):
        return DataDrip(
            pandas.read_json(raw.get("data", ""), orient=cls.orient),
            raw.get("genres", None),
            raw.get("studios", None)
        )

    def __getitem__(self, key: typing.Union[str, typing.Sequence[str]]):
        _key = f"{self.sep}".join(key) if isinstance(key, tuple) else key
        return _key

    def __call__(self):
        return dict(
            data=self.source.to_json(orient=self.orient, date_unit=self.unit),
            genres=self.genres,
            studios=self.studios
        )

    def node(self, *args):
        return self.__getitem__(("node", *args))

    def list_status(self, *args):
        return self.__getitem__(("list_status", *args))

    def purify(self, tz):
        self.source[self["list_status", "spent"]] = \
            self.source[self["node", "average_episode_duration"]] * \
            self.source[self["list_status", "num_episodes_watched"]] / 3600

        self.genres = {}
        self.studios = {}
        genre = self.node("genres")
        studio = self.node("studios")
        updated_at = self.list_status("updated_at")
        start_date = self.node("start_date")
        finish_date = self.node("end_date")
        _time = self.node("broadcast", "start_time")

        self.source[genre], self.source[studio], self.source[updated_at], self.source[start_date], self.source[
            finish_date] = zip(
            *self.source.apply(self.purification, args=(
                tz, genre, studio, updated_at, start_date, finish_date, _time), axis=1)
        )
        self.source.drop(_time, axis=1, inplace=True)

    def purification(self, row, tz, genre, studio, updated_at, start_date, finish_date, __time):
        # ROW WISE
        _time = row[__time]

        results = [
            flat_me(row[genre], self.genres),
            flat_me(row[studio], self.studios),
            str(pandas.to_datetime(row[updated_at], utc=True).astimezone(tz).replace(tzinfo=None))
        ]

        for from_jst in (row[start_date], row[finish_date]):
            if pandas.isnull(from_jst) or pandas.isnull(_time):
                results.append(from_jst if pandas.isnull(_time) else numpy.nan)
                continue

            try:
                b_date, b_time = datetime.strptime(from_jst, "%Y-%m-%d").date(), datetime.strptime(_time, "%H:%M").time()
            except ValueError:
                # MOSTLY BECAUSE OF THE YET TO AIR ANIMES (since they are of form: year-month (2023-04)
                results.append(from_jst)
                continue

            results.append(
                str(datetime.combine(b_date, b_time, tzinfo=timezone("Asia/Tokyo")).astimezone(tz).replace(
                    tzinfo=None)))

        return results


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
        # matching the status with the decoded list status of the User Anime List
        return status if status != "Hold" else "On Hold", numpy.nan if total == "?" else int(total), numpy.nan if watched == "?" else int(watched)

    def gen_id(self, link_node: Tree.Element):
        link = link_node.text
        parsed = re.search(self.id_regex, link)

        return False if not parsed else parsed.group(1)

    def pub_date_to_datetime(self, stamp, time_zone):
        return datetime.strptime(stamp, self.stamp_format).astimezone(timezone(time_zone))

    @classmethod
    def to_frame(cls, what_to_parse: str, time_zone: str):
        parser = XMLParser(what_to_parse)

        records = []

        for item in parser.node.find("channel").iter("item"):
            title = item.find("title").text
            desc = parser.parse_desc(item.find("description"))
            anime_id = parser.gen_id(item.find("link"))
            time_stamp = parser.pub_date_to_datetime(item.find("pubDate").text, time_zone)

            row = (anime_id, title, *desc, time_stamp)

            if not all(row):
                logging.warning("Failed to parse recent animes because of the record: %s, Hence Skipping it", row)
                continue

            records.append(row)

        records.reverse()

        frame = pandas.DataFrame(records, columns=cls.columns)
        calc_cols = iter(cls.calculated_cols)
        frame[next(calc_cols)] = frame[["id", "up_until"]].groupby("id").up_until.diff()

        frame[next(calc_cols)] = frame.difference.isna()
        frame.difference = frame.difference.fillna(1)

        frame[next(calc_cols)] = frame.difference < 0
        frame.difference = frame.difference.abs()

        return frame

    @classmethod
    def from_raw(cls, raw, time_zone) -> typing.Union[bool, pandas.DataFrame]:
        frame = pandas.read_json(raw, orient=bw_json_frame)
        if frame.empty:
            return False
        frame.columns = cls.columns + cls.calculated_cols
        frame.updated_at = pandas.to_datetime(frame.updated_at, utc=True, unit="ms").dt.tz_convert(time_zone)
        return frame


def format_stamp(date, also_for_time=False):
    return "NA" if pandas.isna(date) else date.strftime("%b %d, %Y" if not also_for_time else "%b %d, %Y %H:%M")


def format_rank(rank):
    n = int(rank)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix
