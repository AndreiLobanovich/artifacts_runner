from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
import os

from api.ArtifactsAPI import ArtifactsAPI
from utils import Locations, Slots, skill_to_location


@dataclass
class TMPCharacter:
    name: str
    weapon: str
    tool: str


client = ArtifactsAPI.instance()
get_resource_location = client.get_item_location()


def ensure_logs_directory_exists():
    logs_dir = "./logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)


class Task(ABC):
    location: Locations | None
    item: str | None
    quantity: int
    client: ArtifactsAPI = client
    character: TMPCharacter

    def __init__(self, character: TMPCharacter, quantity, item=None):
        if item:
            self.location = get_resource_location(item)
        self.item = item
        self.quantity = quantity
        self.character: TMPCharacter = character
        print(f'[{self.character.name}] | {self.__class__.__name__} | {self.item} | {self.quantity} created')

    async def __call__(self):
        ensure_logs_directory_exists()
        log_file_name = f"logs/{self.character.name}.log"
        try:
            with open(log_file_name, "a", encoding="utf-8") as logfile:
                logfile.write(
                    f'{self.character.name} starts {self.__class__.__name__} | location: {self.location.name if self.location else "N/A"} | item: {self.item}\n')

            await self.client.move(self.character.name, *self.location.value)
        except Exception as e:
            print(f"Error in {self.__class__.__name__} task: {e}")

    def __del__(self):
        print(f'[{self.character.name}] | {self.__class__.__name__} | {self.item} | {self.quantity} finished')

    def _get_collected_amount(self, item=None):
        try:
            items = self.client.get_char_inventory(self.character.name)
            collected = next(filter(lambda i: i["code"] == (self.item if not item else item), items))["quantity"]
        except:
            collected = 0
        return collected

    async def switch_item(self, slot: Slots, item: str):
        already_equipped = self.client.get_characters_data(self.character.name)[slot.value + "_slot"] == item
        if not already_equipped:
            await self.client.unequip(self.character.name, slot=slot)
            await self.client.equip(self.character.name, item, slot=slot)


class GatherTask(Task):
    def __init__(self, character: TMPCharacter, quantity, item):
        super().__init__(character, quantity, item=item)
        self.collected = self._get_collected_amount(item=self.item)
        self.quantity = self.collected + quantity

    async def __call__(self):
        await super().__call__()
        while self.collected < self.quantity:
            try:
                pillage = self.client.get_map_cell(self.location)["data"]["content"]["type"]
                if pillage == "monster":
                    if self.character.weapon:
                        await self.switch_item(slot=Slots.WEAPON, item=self.character.weapon)
                    await self.client.fight(self.character.name)
                else:
                    if self.character.tool:
                        await self.switch_item(slot=Slots.WEAPON, item=self.character.tool)
                    await self.client.gather_resource(self.character.name)
                with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
                    logfile.write(f'    {"Pillaged" if pillage == "monster" else "Gathered"} {self.collected}/{self.quantity}\n')
                self.collected = self._get_collected_amount(item=self.item)
            except Exception as e:
                print(f"Error in GatherTask: {e}")
                break


class CraftingTask(Task):
    def __init__(
            self,
            character: TMPCharacter,
            quantity,
            location,
            item,
    ):
        super().__init__(character, quantity, item=item)
        self.location = location

    async def __call__(self):
        try:
            recipe = {craft_item["code"]: craft_item["quantity"] for craft_item in self.client.get_item_recipie(self.item)}
            items_to_get_from_bank = dict()
            items_to_get_otherwise = dict()
            for item in recipe:
                if (collected := self._get_collected_amount(item=item)) < (recipe[item] * self.quantity):
                    required = recipe[item] * self.quantity - collected
                    try:
                        left_in_bank = {item["code"]: item["quantity"] for item in self.client.get_bank_items()}[item]
                    except KeyError:
                        left_in_bank = 0
                    if left_in_bank >= required:
                        items_to_get_from_bank.update({item: required})
                    else:
                        if left_in_bank:
                            items_to_get_from_bank.update({item: left_in_bank})
                        if required - left_in_bank > 0:
                            items_to_get_otherwise.update({item: required - left_in_bank})
            if items_to_get_from_bank:
                await RetrieveFromBankTask(self.character, **items_to_get_from_bank)()
            preceding_tasks = []
            for item in items_to_get_otherwise:
                if not client.get_item_recipie(item):
                    preceding_tasks.append(GatherTask(self.character, items_to_get_otherwise[item], item))
                else:
                    item_subtype = client.get_item(item)["craft"]["skill"]
                    location = skill_to_location[item_subtype]
                    preceding_tasks.append(CraftingTask(self.character, items_to_get_otherwise[item], location, item))
            for preceding_task in preceding_tasks:
                await preceding_task()
            await super().__call__()
            await self.client.craft(self.character.name, qtt=self.quantity, code=self.item)
            with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
                logfile.write(f"    Crafted {self.quantity} {self.item}\n")
        except Exception as e:
            print(f"Error in CraftingTask: {e}")


class FightTask(Task):
    progress: int = 0

    def __init__(self, character: TMPCharacter, quantity, location):
        self.location = location
        super().__init__(character, quantity)

    async def __call__(self):
        try:
            await super().__call__()
            log_file_name = f"logs/{self.character.name}.log"
            with open(log_file_name, "a", encoding="utf-8") as logfile:
                for i in range(self.quantity):
                    await self.client.fight(self.character.name)
                    self.progress += 1
                    logfile.write(f'    Killed {self.progress}/{self.quantity}\n')
            self.progress = 0
        except Exception as e:
            print(f"Error in FightTask: {e}")


class DepositTask(Task):
    def __init__(self, character: TMPCharacter, *items):
        super().__init__(character, 0)
        self.items = items
        self.location = Locations.BANK

    async def __call__(self):
        try:
            await super().__call__()
            log_file_name = f"logs/{self.character.name}.log"
            with open(log_file_name, "a", encoding="utf-8") as logfile:
                for item in self.items:
                    amount = self._get_collected_amount(item=item)
                    if not amount:
                        continue
                    await self.client.deposit_item_in_bank(self.character.name, item, amount)
                    logfile.write(f"    Deposited {amount} {item}\n")
        except Exception as e:
            print(f"Error in DepositTask: {e}")


class RetrieveFromBankTask(Task):
    def __init__(self, character: TMPCharacter, **items):
        super().__init__(character, 0)
        self.location = Locations.BANK
        self.items = items

    async def __call__(self):
        try:
            await super().__call__()
            log_file_name = f"logs/{self.character.name}.log"
            with open(log_file_name, "a", encoding="utf-8") as logfile:
                for item in self.items:
                    await self.client.retrieve_item_from_bank(self.character.name, item, self.items[item])
                    logfile.write(f"    Retrieved {item} {self.items[item]}\n")
        except Exception as e:
            print(f"Error in RetrieveFromBankTask: {e}")
