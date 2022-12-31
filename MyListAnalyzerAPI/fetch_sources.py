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

    async def who_is_the_user(self, user_name="", token=""):
        resp = self.get(self.postfix("@me"), headers=dict(Authorization=token)) if token else self.get(
            self.postfix(user_name, "animelist"), headers=self.client_auth, params=dict(
                offset=0, limit=1, sort="list_updated_at"))

        _resp = (await resp).json()
        if not token:
            return user_name, _resp.get("error", "")
        else:
            return _resp["name"], ""
