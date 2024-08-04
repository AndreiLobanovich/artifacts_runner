import json
import os

import requests
from dotenv import load_dotenv
from singleton.singleton import Singleton

from api.urls import *
from utils import Slots, task


@Singleton
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
    def move(self, name, x, y):
        data = {
            "x": x,
            "y": y
        }
        return self._post(MOVE.replace("{name}", name), data)

    @task
    def deposit_item_in_bank(self, name, item_code, qtt):
        data = {
            "code": item_code,
            "quantity": qtt
        }
        return self._post(BANK_DEPOSIT.replace("{name}", name), data=data)

    @task
    def fight(self, name):
        return self._post(FIGHT.replace("{name}", name))

    @task
    def gather_resource(self, name):
        return self._post(GATHER_RESOURCE.replace("{name}", name))

    @task
    def craft(self, name, qtt=1, code="copper_dagger"):
        data = {
            "code": code,
            "quantity": qtt
        }
        return self._post(CRAFT.replace("{name}", name), data=data)

    @task
    def get_new_task(self, name):
        return self._post(NEW_TASK.replace("{name}", name))

    @task
    def unequip(self, name, slot=Slots.WEAPON):
        data = {
            "slot": slot.value
        }
        return self._post(UNEQUIP.replace("{name}", name), data=data)

    @task
    def equip(self, name, item, slot=Slots.WEAPON):
        data = {
            "code": item,
            "slot": slot.value
        }
        return self._post(EQUIP.replace("{name}", name), data=data)

    @task
    def retrieve_item_from_bank(self, name, item, quantity):
        data = {
            "code": item,
            "quantity": quantity
        }
        return self._post(BANK_WITHDRAW.replace("{name}", name), data=data)

    def get_bank_items(self):
        return self._get(BANK_ITEMS).json()["data"]

    def get_all_characters_data(self):
        return self._get(ALL_CHARACTERS_DATA).json()["data"]

    def get_characters_data(self, name):
        data = self._get(ALL_CHARACTERS_DATA).json()["data"]
        char = next(filter(lambda c: c["name"] == name, data))
        return char

    def get_char_inventory(self, name):
        data = self._get(ALL_CHARACTERS_DATA).json()["data"]
        char = next(filter(lambda c: c["name"] == name, data))
        return char["inventory"]

    def get_item(self, item_code):
        data = self._get(ITEM_INFO.replace("{code}", item_code)).json()["data"]["item"]
        return data

    def get_item_recipie(self, item_code):
        return self.get_item(item_code)["craft"]["items"]

    def server_is_up(self):
        try:
            return self._get("/").json()["data"]["status"] == "online"
        except:
            return False
