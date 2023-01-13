import os
import httpx


class MALSession(httpx.AsyncClient):
    api_url = "https://api.myanimelist.net/v2/"

    @property
    def client_id(self):
        return os.getenv("MAL_CLIENT_ID")

    @property
    def client_auth(self):
        return {"X-MAL-CLIENT-ID": self.client_id}

    def postfix(self, *then, fix="users"):
        return self.api_url + fix + "/" + "/".join(then)

    def set_headers(self, token):
        self.headers.update(dict(Authorization=token) if token else self.client_auth)

    async def who_is_the_user(self, user_name="", token=""):
        self.set_headers(token)
        resp = self.get(self.postfix("@me")) if token else self.get(
            self.postfix(user_name, "animelist"), params=dict(
                offset=0, limit=1, sort="list_updated_at"))

        _resp = (await resp).json()
        if not token:
            return user_name, _resp.get("error", "")
        else:
            return _resp["name"], ""

    async def fetch_list(self, user_name, token=None, embed_url=None, sort_order="list_updated_at", offset=0, limit=1e3):
        self.set_headers(token)
        fields = "genres,list_status{start_date,finish_date,num_times_rewatched,rewatch_value,priority,score}," \
                 "start_date,end_date,mean,rank,popularity,created_at,updated_at,num_episodes,media_type,source," \
                 "average_episode_duration,rating,studios,start_season,nsfw,status," \
                 "broadcast,num_scoring_users,num_list_users,num_favorites"
        resp = self.get(
            self.postfix(user_name, "animelist"), params={
                "sort": sort_order,
                "fields": fields,
                "offset": offset,
                "limit": limit
            }
        ) if not embed_url else self.get(embed_url)

        _resp = (await resp).json()
        assert "error" not in _resp, _resp.get("error", "Empty Response")

        next_page = _resp.get("paging", {}).get("next", "")
        _raw = _resp.get("data", [])

        for row in _raw:
            row["node"].get("main_picture", dict(medium="")).pop("medium")
            row["node"].get("broadcast", dict(day_of_the_week="")).pop("day_of_the_week")

        return dict(raw=_raw, next_page=next_page, user_name=user_name)
