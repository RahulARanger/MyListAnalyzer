import statistics as stat
import typing
from datetime import datetime
import numpy
import numpy as np
import pandas
from pytz import timezone
from MyListAnalyzerAPI.modals import ep_range_bin, rating
from MyListAnalyzerAPI.utils import DataDrip, format_stamp


def list_status(drip: DataDrip):
    status_index = drip["list_status", "status"]
    collected = pandas.DataFrame(drip.source[status_index].value_counts())
    collected["%"] = (collected.values / collected.values.sum()) * 100
    return collected


def airing_status(drip: DataDrip):
    title = drip.node("title")
    watched = drip.list_status("num_episodes_watched")
    total = drip.node("num_episodes")
    updated_at = drip.list_status("updated_at")
    source = drip.node("source")
    a_status = drip.node("status")
    picture = drip.node("main_picture", "large")
    status = drip.list_status("status")
    start_date = drip.node("start_date")
    l_start_date = drip.list_status("start_date")

    if l_start_date not in drip.source.columns:
        # in case if user has no start date for at least one of the animes in the list
        drip.source[l_start_date] = np.nan

    sliced = drip.source.loc[:, [title, picture, start_date, l_start_date, watched, total, updated_at, source, status]][
        drip.source[a_status] == "currently_airing"].head(10).sort_values(status)

    start_dates = pandas.to_datetime(sliced.pop(start_date))
    sliced["day"] = start_dates.dt.day_name()
    sliced["time"] = start_dates.dt.strftime("%H:%M")
    sliced["date"] = format_stamp(start_dates.dt)
    sliced[l_start_date] = format_stamp(pandas.to_datetime(sliced[l_start_date]).dt)

    sliced.to_json(orient="split")

    _id = drip.node("id")
    _slice = drip.source[_id][drip.source[a_status] == "not_yet_aired"]

    return (
        int(_slice.shape[0]),
        sliced.to_json(orient="split")
    )


async def report_gen(tz: str, drip: DataDrip):
    # PRE REQUISITES
    for dates in (drip.list_status("updated_at"), drip.node("start_date")):
        drip.source[dates] = pandas.to_datetime(drip.source[dates])
    # D-TYPE CONVERSION COMPLETED (if required for all values)

    status = list_status(drip)
    ep_range = extract_ep_bins(drip)

    not_yet_aired, animes_airing = airing_status(drip)

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
        ep_range=ep_range.to_json(orient="index"),
        mostly_seen_genre=drip.genres[genres_mode],
        mostly_seen_studio=drip.studios[studios_mode],
        avg_score=0 if np.isnan(avg_score) else avg_score,
        eps_watched=watched,
        genre_link=genres_mode,
        studio_link=studios_mode,
        current_year=datetime.now(timezone(tz)).year,
        rating_dist=rating_dist.to_json(orient="index"),
        specials=special_animes_report(drip),
        currently_airing_animes=animes_airing
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

    # so result {"index": [...bins], "data": [...bin_values]}
    extracted.set_index("key_0", inplace=True, drop=True)
    return extracted.loc[:, "ep_range"]


async def process_recent_animes_by_episodes(
        recent_animes: pandas.DataFrame
):
    week_days, week_dist, first_record, recent_record = parse_weekly(recent_animes)

    grouped_by_updated_at = recent_animes.iloc[:, 3:]

    recently_updated_day_wise = recently_updated_freq(
        grouped_by_updated_at, "difference")

    return dict(
        first_record=first_record.timestamp(), recent_record=recent_record.timestamp(),
        week_days=week_days, week_dist=week_dist,
        recently_updated_day_wise=recently_updated_day_wise.T.to_json(orient="split"),
        special_results=special_results_for_recent_animes(recent_animes)
    )


def parse_weekly(recent_animes: pandas.DataFrame):
    sliced = recent_animes.loc[:, ["updated_at", "difference"]].groupby(
        recent_animes.updated_at.dt.day_of_week).difference.sum()

    weeks = pandas.Series(0, index=numpy.arange(7), name="_w")
    sliced = pandas.merge(weeks, sliced, left_on=weeks.index, right_on=sliced.index, how="left")

    first_record = recent_animes.updated_at.min()
    recent_record = recent_animes.updated_at.max()

    dist = tuple(busy_day_count(first_record.date(), (recent_record + pandas.Timedelta(days=1)).date()))
    return dist, sliced.difference.to_json(orient="values"), first_record, recent_record


def recently_updated_freq(recent_animes: pandas.DataFrame, col="difference"):
    # first two columns are id and title
    updated_freq = recent_animes.groupby(
        [
            recent_animes.updated_at.dt.year,
            recent_animes.updated_at.dt.month,
            recent_animes.updated_at.dt.day
        ]
    ).sum(col)

    return updated_freq


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
    ), drip.node("id"), drip.node("main_picture", "large")

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
                format_stamp(pandas.to_datetime(entity.get(_))) if not pandas.isnull(entity.get(_, np.nan)) else "NA"
            ) for _ in info_parameters[: -1]
        ]

        info.append(
            format_stamp(pandas.to_datetime(entity.get(info_parameters[-1])), True)
            if entity.get(info_parameters[-1], "") else "NA"
        )

        results[key] = dict(
            general=[str(entity.get(_, "")) for _ in general_parameters],
            progress=[int(entity.get(_, 0)) for _ in progress_parameters] + [
                entity.get(drip.list_status("status"), "")],
            required_parameters=required,
            special=special,
            info=info
        )

    return results


def busy_day_count(start_date, end_date) -> typing.List[int]:
    """
    Returns the Distribution of week days from start date and end date
    :param start_date: start_date is included
    :param end_date: end_date is excluded
    :return:
    """
    weeks = numpy.zeros(7)

    for index in range(weeks.size):
        weeks[index] += 1
        yield int(numpy.busday_count(start_date, end_date, weekmask=weeks))
        weeks[index] -= 1


def special_results_for_recent_animes(recent_animes: pandas.DataFrame):
    anime_first_updated = recent_animes.groupby("id").first()
    anime_last_updated = recent_animes.groupby("id").last()
    results = dict(recent=str(recent_animes.iloc[-1].id))

    for _status in ("Watching", "Completed", "Dropped", "Hold"):
        sliced = recent_animes[recent_animes.status == _status]
        if sliced.empty:
            continue

        results[_status] = sliced.iloc[-1].to_json(orient="values")

    sliced = recent_animes.id.value_counts()[::-1]
    results["many_records"] = dict(
        mode=int(sliced.max()),
        anime=recent_animes[recent_animes.id == sliced.idxmax()].iloc[-1].to_json(orient="values")
    )

    results["most_updated"] = recent_animes.iloc[recent_animes.loc[::-1].difference.idxmax()].to_json(orient="values")

    anime_id = (anime_last_updated.updated_at - anime_first_updated.updated_at).idxmax()

    results["long_time"] = dict(
        anime=anime_first_updated.loc[anime_id].to_json(orient="values"),
        time_took=str(anime_last_updated.loc[anime_id, "updated_at"] - anime_first_updated.loc[anime_id, "updated_at"]),
        id=str(anime_id)
    )

    re_ = anime_last_updated.loc[::-1]
    the_one = (anime_last_updated.total - anime_first_updated.up_until).idxmax()
    results["large_change"] = dict(
        anime=re_.loc[the_one].to_json(orient="values"),
        id=str(the_one)
    )

    results["longest_title"] = recent_animes.iloc[recent_animes.title.str.len().idxmax()].to_json(orient="values")

    return results
