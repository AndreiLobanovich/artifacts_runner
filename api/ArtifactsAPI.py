import json
import os

import requests
from dotenv import load_dotenv

from api.urls import *
from utils import Slots, task


class ArtifactsAPI:
    ROOT_URL = "https://api.artifactsmmo.com"

    def __init__(self):
        load_dotenv()
        token = os.environ.get("API_TOKEN")

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

    def _post(self, url, data=None):
        if data is None:
            data = dict()
        return requests.post(self.ROOT_URL + url, headers=self.headers, data=json.dumps(data), allow_redirects=True)

    def _get(self, url):
        return requests.get(self.ROOT_URL + url, headers=self.headers)

    @task
    def move(self, x, y, name, url=MOVE):
        data = {
            "x": x,
            "y": y
        }
        return self._post(url.replace("{name}", name), data)

    @task
    def fight(self, name, url=FIGHT):
        return self._post(url.replace("{name}", name))

    @task
    def gather_resource(self, name, url=GATHER_RESOURCE):
        return self._post(url.replace("{name}", name))

    @task
    def craft(self, name, url=CRAFT, qtt=1, code="copper_dagger"):
        data = {
            "code": code,
            "quantity": qtt
        }
        return self._post(url.replace("{name}", name), data=data)

    @task
    def get_new_task(self, name, url=NEW_TASK):
        return self._post(url.replace("{name}", name))

    @task
    def unequip(self, name, url=UNEQUIP, slot=Slots.WEAPON):
        data = {
            "slot": slot.value
        }
        return self._post(url.replace("{name}", name), data=data)

    def get_char_inventory(self, name):
        data = self._get(CHARACTER_INFO).json()["data"]
        char = next(filter(lambda c: c["name"] == name, data))
        return char["inventory"]

    def get_item(self, item_code):
        data = self._get(CHARACTER_INFO.replace("{code}", item_code)).json()["data"]["item"]
        return data
