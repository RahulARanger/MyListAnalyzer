import pandas
import typing
from MyListAnalyzerAPI.utils import DataDrip
from datetime import datetime
from pytz import timezone


def list_status(drip: DataDrip):
    status_index = drip["list_status", "status"]
    collected = pandas.DataFrame(drip.source[[status_index]].groupby(status_index).value_counts())
    collected["%"] = (collected.values / collected.values.sum()) * 100
    return collected


def not_finished_airing(drip: DataDrip):
    n_s = drip["node", "status"]
    l_s = drip["list_status", "status"]

    # we don't need finished ones
    status_maps = pandas.DataFrame(drip.source[[l_s, n_s]][drip.source[n_s] != "finished_airing"])

    return (int((status_maps[n_s] == "not_yet_aired").shape[0]),
            status_maps[status_maps[n_s] == "currently_airing"][[l_s]].groupby(l_s).value_counts())


def report_gen(drip: DataDrip, tz: str):
    status = list_status(drip)

    ep = drip["list_status", "num_episodes_watched"]
    ep_range = drip.source[drip.source[ep] != 0][ep]
    not_yet_aired, currently_airing = not_finished_airing(drip)

    season = drip["node", "start_season", "season"]
    start_year = drip["node", "start_season", "year"]

    current_year = datetime.now(timezone(tz)).year

    seasons = pandas.DataFrame(drip.source[[season]].groupby(season).value_counts())[0]
    this_year = drip.source[drip.source[start_year] == current_year][[season]].groupby(season).value_counts()

    return {
        "row_1": {
            "values": [
                int(drip.source.shape[0]),
                float(drip.source[drip["list_status", "spent"]].sum()), int(status.loc["watching", 0]),
                not_yet_aired
            ],
            "keys": ["Total Animes", "Time spent (hrs)", "Watching", "Not Yet Aired"]
        },
        "row_2": status[status.index != "watching"].to_json(orient="split"),
        "row_3": [
            ep_range.to_list(),
            currently_airing.to_json(orient="split"),
            [
                seasons.to_json(orient="split"), this_year.to_json(orient="split")
            ]
        ]
    }
