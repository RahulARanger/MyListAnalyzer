import pandas
import typing
from MyListAnalyzerAPI.utils import DataDrip
from MyListAnalyzerAPI.modals import ep_range_bin
from datetime import datetime
from pytz import timezone
import numpy as np


def list_status(drip: DataDrip):
    status_index = drip["list_status", "status"]
    collected = pandas.DataFrame(drip.source[[status_index]].groupby(status_index).value_counts())
    collected["%"] = (collected.values / collected.values.sum()) * 100
    return collected


def not_finished_airing(drip: DataDrip):
    n_s = drip["node", "status"]
    l_s = drip["list_status", "status"]
    name = drip["node", "title"]
    pic = drip["node", "main_picture", "medium"]

    # we don't need finished ones
    status_maps = pandas.DataFrame(drip.source[[l_s, n_s, name, pic]][drip.source[n_s] != "finished_airing"])
    currently_airing = status_maps[status_maps[n_s] == "currently_airing"]

    return (
        int((status_maps[n_s] == "not_yet_aired").shape[0]),
        currently_airing.loc[:, [l_s]].groupby(l_s).value_counts(),
        currently_airing.loc[:, [name, pic, l_s]])


async def report_gen(drip: DataDrip, tz: str = "Asia/Japan"):
    status = list_status(drip)

    ep_range = extract_ep_bins(drip)

    not_yet_aired, currently_airing, animes_airing = not_finished_airing(drip)

    season = drip["node", "start_season", "season"]
    start_year = drip["node", "start_season", "year"]

    current_year = datetime.now(timezone(tz)).year

    seasons = ensure_seasons(
        pandas.DataFrame(drip.source[[season]].groupby(season).value_counts())
    )
    this_year = ensure_seasons(
        pandas.DataFrame(drip.source[drip.source[start_year] == current_year][[season]].groupby(season).value_counts())
    )

    hrs_spent = float(drip.source[drip["list_status", "spent"]].sum())

    return {
        "row_1": {
            "values": [
                int(drip.source.shape[0]),
                int(status.loc["watching", 0]),
                not_yet_aired
            ],
            "keys": ["Total Animes", "Watching", "Not Yet Aired"]
        },
        "time_spent": [
            [hrs_spent, "Time spent (hrs)"],
            [hrs_spent / 24, "Time spent (days)"]
        ],
        "row_2": status[status.index != "watching"].to_json(orient="split"),
        "row_3": [
            ep_range.to_json(orient="split"),
            [seasons.to_json(orient="split"), this_year.to_json(orient="split")],
            currently_airing.to_json(orient="split"),
            animes_airing.to_json(orient="records"), current_year
        ]
    }


def ensure_seasons(collected: pandas.DataFrame, as_percent=True, values_col=0):
    collected = collected.reindex(["spring", "summer", "fall", "winter"])

    if as_percent:
        total = collected[values_col].sum()
        collected["%"] = collected[values_col] / total

    return collected


def extract_ep_bins(drip: DataDrip):
    ep = drip["list_status", "num_episodes_watched"]

    # animes of 0 episodes are excluded maybe those are planned to be aired.

    ep_range = pandas.DataFrame(drip.source[drip.source[ep] != 0][[ep]])

    # these are the ranges, manually set please suggest good bins.
    ep_range_bin_labels = np.array([
        "<12", "12-24", "25-100", "101-200", "201-500", ">500"
    ])

    # index to labels
    ep_range[ep] = ep_range_bin_labels[np.digitize(ep_range[ep], ep_range_bin)]

    ep_range = ep_range.groupby(ep).value_counts()
    ep_range["color"] = np.where(ep_range == ep_range.max(), "crimson", "lightslategray")
    # it's not like I blindly copied those colors, its just I like. Suggest any colors if needed please.

    # note above one doesn't add a column instead adds a row in the group-by variable
    # as it is not pandas dataframe
    # so result {"index": [...bins, "colors"], "data": [...bin_values, ["red", ... "orange"]]}

    return ep_range
