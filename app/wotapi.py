import datetime

from fastapi import status
from requests import (
    Request,
    Response,
    request,
)

from .exceptions import HTTPException
from .user import User

"""
# @TODO
# Implement rate limit handling
# switch to requests.Session
# improve exception handling
"""


class WoTAPI:
    def __init__(self, app_id: str, clan_id: int) -> None:
        self.baseURL = "https://api.worldoftanks.eu/wot/"
        self.headers = {"User-Agent": "tankU-clan/python-requests"}
        self.appID = f"?application_id={app_id}"
        self.clanID = clan_id

    def _call(
        self,
        method: str,
        endpoint: str,
        params: dict | None = {},
        data: dict | None = {},
    ) -> dict | HTTPException:
        print(f"{datetime.datetime.now()}: {method} {endpoint} called")
        resp = request(
            method,
            self.baseURL + endpoint + self.appID,
            params=params,
            data=data,
            headers=self.headers,
        )
        return self._validate_response(resp)

    def _validate_response(self, resp: Response) -> dict | HTTPException:
        if not resp.ok or resp.json()["status"] == "error":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f'WoT API returned status code: {resp.json()["error"]["code"]}',
                resp.json()["error"],
            )
        else:
            return resp.json()

    def verify_user_token(self, access_token: str, nickname: str, account_id: int) -> bool:
        endpoint = "account/info/"
        params = {
            "account_id": account_id,
            "access_token": access_token,
            "fields": "nickname",
        }

        try:
            resp = self._call(method="GET", endpoint=endpoint, params=params)
        except HTTPException:
            return False
        else:
            return True if resp["data"][str(account_id)]["nickname"] == nickname else False

    def extend_access_token(self, user: User) -> dict | HTTPException:
        endpoint = "auth/prolongate/"
        data = {"access_token": user.access_token, "expires_at": 1209500}

        try:
            resp = self._call(method="POST", endpoint=endpoint, data=data)
        except HTTPException:
            raise
        else:
            return resp["data"]

    def get_online_member_count(self, user: User) -> int | HTTPException:
        endpoint = "clans/info/"
        params = {
            "clan_id": self.clanID,
            "access_token": user.access_token,
            "extra": "private.online_members",
            "fields": "private.online_members",
        }

        try:
            resp = self._call(method="GET", endpoint=endpoint, params=params)
        except HTTPException:
            raise
        else:
            return len(resp["data"][str(self.clanID)]["private"]["online_members"])

    def get_clan_booster_status(self, user: User) -> dict | HTTPException:
        raise NotImplementedError

    def activate_clan_booster(self, user: User, *boosters: str | None) -> bool | HTTPException:
        endpoint = "stronghold/activateclanreserve/"
        data = {"access_token": user.access_token, "reserve_level": 10}

        for booster in boosters:
            if booster:
                data["reserve_type"] = booster

                try:
                    self._call(method="POST", endpoint=endpoint, data=data)
                except HTTPException:
                    raise
                else:
                    return True
