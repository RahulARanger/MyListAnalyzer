import statistics as stat
from datetime import datetime
import numpy
import numpy as np
import pandas
from pytz import timezone
from MyListAnalyzerAPI.modals import ep_range_bin, bw_json_frame, rating
from MyListAnalyzerAPI.utils import DataDrip, format_stamp


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
    # PRE REQUISITES
    for dates in (drip.list_status("updated_at"), drip.node("start_date")):
        drip.source[dates] = pandas.to_datetime(drip.source[dates])
    # D-TYPE CONVERSION COMPLETED (if required for all values)

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

    grouped_by_updated_at = recent_animes.iloc[:, 3:]

    recently_updated_day_wise, recently_updated_cum_sum = recently_updated_freq(
        grouped_by_updated_at, "difference")

    return dict(
        recently_updated_at=recently_updated_at,
        recently_updated_day_wise=recently_updated_day_wise.T.to_json(orient="split"),
        recently_updated_cum_sum=recently_updated_cum_sum.to_list()
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


def special_animes_report(drip: DataDrip):
    progress_parameters = drip.node(
        "num_episodes"
    ), drip.list_status(
        "num_episodes_watched"
    ), drip.list_status(
        "spent"
    )

    required_parameters = drip.node(
        "num_favorites"
    ), drip.node(
        "start_date"
    ), drip.node(
        "end_date"
    )

    general_parameters = drip.node(
        "title"
    ), drip.node("id"), drip.node("main_picture.large")

    info_parameters = drip.list_status(
        "start_date"
    ), drip.list_status("finish_date"), drip.list_status("updated_at")

    results = {}

    # MOST POPULAR ANIME
    popular = drip.source.loc[drip.source[drip.node("popularity")].idxmin()]
    pop_value = str(popular.get(drip.node("popularity"))), "Popularity Rank"

    # MOST RECENTLY UPDATED ANIME
    recent = drip.source.loc[drip.source[drip.list_status("updated_at")].idxmax()]
    recent_value = [recent.get(drip.list_status("updated_at")), "Updated Stamp"]
    recent_value[0] = "NA" if not recent_value[0] else format_stamp(recent_value[0])

    # TOP SCORED ANIME
    top = drip.source.loc[drip.source[drip.node("rank")].idxmin()]
    rank = str(top.get(drip.node("rank"))), "Rank"

    # OLDEST ANIME IN THE LIST
    oldest = drip.source.loc[drip.source[drip.node("start_date")].idxmin()]
    start_date = [oldest.get(drip.node("start_date")), "Started at"]
    start_date[0] = "NA" if not start_date[0] else format_stamp(start_date[0])
    # Mostly we don't need to apply timezone as the start date has no info about the time

    # ANIME THE USER HAS SPENT THE LONGEST TIME WITH
    longest_spent = drip.source.loc[drip.source[drip.list_status("spent")].idxmax()]
    spent = f"{float(longest_spent.get(drip.list_status('spent')))} hrs", "Longest Time Spent"

    # RECENTLY COMPLETED MOVIE
    watched_movies = drip.source[
        (drip.source[drip.node("media_type")] == "movie") & (drip.source[drip.list_status("status")] == "completed")]
    recently_completed_movie = None if watched_movies.empty else watched_movies.loc[
        watched_movies[drip.list_status("updated_at")].idxmax()]
    recent_movie_stamp = "" if recently_completed_movie is None else recently_completed_movie.get("updated_at", "")
    recent_movie_stamp = (
        "NA" if not recent_movie_stamp else format_stamp(recent_movie_stamp), "Mostly Seen Movie"
    )

    for entity, key, special in zip(
            (popular, recent, top, oldest, longest_spent),
            ("pop", "recent", "top", "oldest", "longest_spent", "recently_completed_movie"),
            (pop_value, recent_value, rank, start_date, spent, recent_movie_stamp)

    ):
        required = [
            (
                format_stamp(pandas.to_datetime(entity.get(_))) if entity.get(_, "") else "NA"
            ) for _ in required_parameters[1:]
        ]
        fav_s = entity.get(required_parameters[0])
        required.insert(0, int(fav_s) if fav_s else "NA")

        info = [
            (
                format_stamp(pandas.to_datetime(entity.get(_))) if entity.get(_, "") else "NA"
            ) for _ in info_parameters[: -1]
        ]

        info.append(
            format_stamp(pandas.to_datetime(entity.get(info_parameters[-1])), True)
            if entity.get(info_parameters[-1], "") else "NA"
        )

        results[key] = dict(
            general=[str(entity.get(_, "")) for _ in general_parameters],
            progress=[int(entity.get(_, 0)) for _ in progress_parameters] + [entity.get(drip.list_status("status"), "")],
            required_parameters=required,
            special=special,
            info=info
        )

    return results
