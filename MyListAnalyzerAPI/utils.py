import typing
import numpy
import pandas


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
            pandas.read_json(raw.get("data", ""), orient="columns"), raw.get("genres", None), raw.get("studios", None)
        )

    def __getitem__(self, key: typing.Union[str, typing.Sequence[str]]):
        _key = f"{self.sep}".join(key) if isinstance(key, tuple) else key
        return _key

    def __call__(self):
        return {"data": self.source.to_json(orient="columns"), "genres": self.genres, "studios": self.studios}
