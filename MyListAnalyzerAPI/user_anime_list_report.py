import statistics as stat
from datetime import datetime
import numpy
import numpy as np
import pandas
from pytz import timezone
from MyListAnalyzerAPI.modals import ep_range_bin, bw_json_frame, rating
from MyListAnalyzerAPI.utils import DataDrip


def list_status(drip: DataDrip):
    status_index = drip["list_status", "status"]
    collected = pandas.DataFrame(drip.source[status_index].value_counts())
    collected["%"] = (collected.values / collected.values.sum()) * 100
    return collected


def not_finished_airing(drip: DataDrip):
    watchers = drip.node("status")
    l_s = drip.list_status("status")
    name = drip.node("title")

    # we don't need finished ones
    status_maps = pandas.DataFrame(drip.source[[l_s, watchers, name]][drip.source[watchers] != "finished_airing"])
    currently_airing = status_maps[status_maps[watchers] == "currently_airing"]

    return (
        int((status_maps[watchers] == "not_yet_aired").shape[0]),
        currently_airing.loc[:, l_s].value_counts(),
        currently_airing.loc[:, [name, l_s]])


async def report_gen(tz: str, drip: DataDrip):
    # drip.prepare_time_stamps(tz)
    status = list_status(drip)
    ep_range = extract_ep_bins(drip)

    not_yet_aired, currently_airing, animes_airing = not_finished_airing(drip)

    hrs_spent = float(drip.source[drip.list_status("spent")].sum())

    score_index = drip.list_status("score")
    genres_mode = str(int(stat.mode(np.concatenate(drip.source[drip.node("genres")].to_numpy()))))
    studios_mode = str(int(stat.mode(np.concatenate(drip.source[drip.node("studios")].to_numpy()))))

    watched = int(drip.source[drip.list_status("num_episodes_watched")].sum())
    avg_score = drip.source[score_index][drip.source[score_index] > 0].mean()

    rating_dist = drip.source[drip.node("rating")].value_counts().convert_dtypes()
    rating_dist.index = rating_dist.index.map(rating)

    return dict(
        row_1=dict(
            values=[
                int(drip.source.shape[0]),
                int(status[drip.list_status("status")].get("watching", 0)),
                not_yet_aired
            ],
            keys=["Total Animes", "Watching", "Not Yet Aired"]
        ),
        time_spent=[
            [hrs_spent, "Time spent (hrs)"],
            [hrs_spent / 24, "Time spent (days)"]
        ],
        row_2=status[status.index != "watching"].to_json(orient="split"),
        ep_range=ep_range.to_json(orient="columns"),
        status_for_currently_airing=currently_airing.to_json(orient="split"),
        rating_over_years=rating_over_years(drip),
        mostly_seen_genre=drip.genres[genres_mode],
        mostly_seen_studio=drip.studios[studios_mode],
        avg_score=0 if np.isnan(avg_score) else avg_score,
        eps_watched=watched,
        genre_link=genres_mode,
        studio_link=studios_mode,
        current_year=datetime.now(timezone(tz)).year,
        rating_dist=rating_dist.to_json(orient="index"),
        specials=special_animes_report(drip)
    )


def extract_ep_bins(drip: DataDrip):
    ep = drip.node("num_episodes")

    # animes of 0 episodes are excluded maybe those are planned to be aired.

    ep_range = pandas.DataFrame(drip.source[[ep]][drip.source[ep] != 0])
    ep_range_bin_labels = pandas.Series(0, index=[
        "<12", "12-24", "25-100", "101-200", "201-500", ">500"
    ], name="index")

    # index to labels
    ep_range[ep] = ep_range_bin_labels.index[numpy.digitize(ep_range[ep], ep_range_bin)]

    ep_range = ep_range[ep].value_counts().rename("ep_range")

    extracted = pandas.merge(
        ep_range_bin_labels, ep_range, right_on=ep_range.index, left_on=ep_range_bin_labels.index, how="left",
        suffixes=("_", "_actual")
    )
    extracted["color"] = extracted.ep_range == extracted.ep_range.max()

    # so result {"index": [...bins, "colors"], "data": [...bin_values, ["red", ... "orange"]]}

    return extracted.loc[:, ["key_0", "color", "ep_range"]]


async def process_recent_animes_by_episodes(
        recent_animes: pandas.DataFrame
):
    recently_updated_at = recent_animes.updated_at.max().timestamp()

    # 10 recently updated animes
    recently_updated = recent_animes[
                           ["id", "title", "updated_at", "up_until", "difference", "status", "total", "re_watched"]
                       ].tail(10).iloc[::-1]

    grouped_by_updated_at = recent_animes.iloc[:, 3:]

    recently_updated_day_wise, recently_updated_cum_sum = recently_updated_freq(
        grouped_by_updated_at, "difference")

    return dict(
        recently_updated_at=recently_updated_at,
        recently_updated_animes=recently_updated.to_json(
            orient=bw_json_frame, date_unit="s"),
        recently_updated_day_wise=recently_updated_day_wise.T.to_json(orient="split"),
        recently_updated_cum_sum=recently_updated_cum_sum.to_list(),
        stamps=recent_animes.updated_at.to_json(date_unit="s")
    )


def recently_updated_freq(recent_animes: pandas.DataFrame, col="difference"):
    # first two columns are id and title
    updated_freq = recent_animes.groupby(
        [
            recent_animes.updated_at.dt.year,
            recent_animes.updated_at.dt.month,
            recent_animes.updated_at.dt.day
        ]
    ).sum(col)

    return updated_freq, updated_freq[col].cumsum()


def rating_over_years(drip: DataDrip):
    updated_at = drip.source[drip.list_status("updated_at")]

    collected = drip.source[[drip.node("rating")]].groupby(
        [updated_at.dt.year, updated_at.dt.month, drip.node("rating")]).value_counts().sort_index()

    # https://myanimelist.net/forum/?topicid=2039350
    ratings = ["pg", "pg_13", "g", "r", "r+", "rx"]

    payload = dict(ratings=ratings, years=[], months=[], frames=[])

    for year, month in zip(collected.index.get_level_values(0), collected.index.get_level_values(1)):
        prev = payload["frames"][-1] if payload["frames"] else ([0] * len(ratings))
        payload["years"].append(year)
        payload["months"].append(month)
        payload["frames"].append(
            [
                int(collected.get((year, month, rating), 0)) + prev[index]
                for index, rating in enumerate(ratings)
            ]
        )

    payload["max_y_range"] = max(payload["frames"][-1])

    return payload


def special_animes_report(drip: DataDrip):
    pop = drip.source.loc[drip.source[drip.node("popularity")].idxmin()]
    recent = drip.source.loc[drip.source[drip.list_status("updated_at")].idxmax()]
    top = drip.source.loc[drip.source[drip.node("rank")].idxmin()]
    oldest = drip.source.loc[drip.source[drip.node("start_date")].astype("datetime64[ns]").idxmin()]
    longest_spent = drip.source.loc[drip.source[drip.list_status("spent")].idxmax()]

    watched_movies = drip.source[
        (drip.source[drip.node("media_type")] == "movie") & (drip.source[drip.list_status("status")] == "completed")]
    recently_completed_movie = None if watched_movies.empty else watched_movies.loc[watched_movies[drip.list_status("updated_at")].idxmax()]

    return dict(
        pop=pop.to_json(), recent=recent.to_json(),
        top=top.to_json(), oldest=oldest.to_json(),
        longest_spent=longest_spent.to_json(),
        recently_completed_movie=recently_completed_movie.to_json() if recently_completed_movie else False
    )
