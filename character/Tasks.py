from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from api.ArtifactsAPI import ArtifactsAPI
from utils import Locations, Slots


@dataclass
class TMPCharacter:
    name: str
    weapon: str
    tool: str


class Task(ABC):
    location: Locations | None
    item: str | None
    quantity: int

    def __init__(self, character: TMPCharacter, quantity, location=None, item=None):
        self.location = location
        self.item = item
        self.quantity = quantity
        self.character: TMPCharacter = character
        print(f'[{self.character}] | {self.__class__.__name__} created')

    def __del__(self):
        print(f'[{self.character}] | {self.__class__.__name__} finished')

    async def __call__(self, client: ArtifactsAPI):
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            logfile.write(
                f'{self.character.name} starts {self.__class__.__name__} | location: {self.location} | item: {self.item}\n')
        await client.move(self.character.name, *self.location.value)

    def _get_collected_amount(self, client: ArtifactsAPI, item=None):
        try:
            items = client.get_char_inventory(self.character.name)
            collected = next(filter(lambda i: i["code"] == (self.item if not item else item), items))["quantity"]
        except:
            collected = 0
        return collected

    async def switch_item(self, client, slot: Slots, item: str):
        already_equipped = client.get_characters_data(self.character.name)[slot.value + "_slot"] == item
        if not already_equipped:
            await client.unequip(self.character.name, slot=slot)
            await client.equip(self.character.name, item, slot=slot)


class GatherTask(Task):
    def __init__(self, character: TMPCharacter, quantity, location, item, pillage=False):
        super().__init__(character, quantity, location=location, item=item)
        self.pillage = pillage

    async def __call__(self, client: ArtifactsAPI):
        await super().__call__(client)
        while (collected := self._get_collected_amount(client, item=self.item)) < self.quantity:
            if self.pillage:
                if self.character.weapon:
                    await self.switch_item(client, slot=Slots.WEAPON, item=self.character.weapon)
                await client.fight(self.character.name)
            else:
                if self.character.tool:
                    await self.switch_item(client, slot=Slots.WEAPON, item=self.character.tool)
                await client.gather_resource(self.character.name)
            with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
                logfile.write(f'    {"Pillaged" if self.pillage else "Gathered"} {collected}/{self.quantity}\n')


class CraftingTask(Task):
    def __init__(
            self,
            character: TMPCharacter,
            quantity,
            location,
            item,
            prep_tasks: list[GatherTask | "CraftingTask"]
    ):
        super().__init__(character, quantity, location=location, item=item)
        self.prep_tasks = prep_tasks

    async def __call__(self, client: ArtifactsAPI):
        # prep for crafting
        recipie = {craft_item["code"]: craft_item["quantity"] for craft_item in client.get_item_recipie(self.item)}
        items_to_get_from_bank = dict()
        items_to_get_otherwise = {}
        for item in recipie:
            if (collected := self._get_collected_amount(client, item=item)) < (recipie[item] * self.quantity):
                required = recipie[item] * self.quantity - collected
                try:
                    left_in_bank = {item["code"]: item["quantity"] for item in client.get_bank_items()}[item]
                except KeyError:
                    left_in_bank = 0
                if left_in_bank >= required:
                    items_to_get_from_bank.update({item: required})
                else:
                    items_to_get_otherwise.update({item: required})
        if items_to_get_from_bank:
            await RetrieveFromBankTask(self.character, **items_to_get_from_bank)(client)
            await client.move(self.character.name, *self.location.value)
        prep_tasks = list(filter(lambda t: t.item in items_to_get_otherwise, self.prep_tasks))
        for prep_task in prep_tasks:
            await prep_task(client)
        # crafting itself
        await super().__call__(client)
        await client.craft(self.character.name, qtt=self.quantity, code=self.item)
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            logfile.write(f"    Crafted {self.quantity} {self.item}\n")


class FightTask(Task):
    progress: int = 0

    def __init__(self, character: TMPCharacter, quantity, location):
        super().__init__(character, quantity, location=location)

    async def __call__(self, client: ArtifactsAPI):
        await super().__call__(client)
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            for i in range(self.quantity):
                await client.fight(self.character.name)
                self.progress += 1
                logfile.write(f'    Killed {self.progress}/{self.quantity}')
        self.progress = 0


class DepositTask(Task):
    def __init__(self, character: TMPCharacter, *items):
        super().__init__(character, 0, location=Locations.BANK)
        self.items = items

    async def __call__(self, client: ArtifactsAPI):
        await super().__call__(client)
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            for item in self.items:
                amount = self._get_collected_amount(client, item=item)
                if not amount:
                    continue
                await client.deposit_item_in_bank(self.character.name, item, amount)
                logfile.write(f"    Deposited {amount} {item}\n")


class RetrieveFromBankTask(Task):
    def __init__(self, character: TMPCharacter, **items):
        super().__init__(character, 0, location=Locations.BANK)
        self.items = items

    async def __call__(self, client: ArtifactsAPI):
        await super().__call__(client)
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            for item in self.items:
                await client.retrieve_item_from_bank(self.character.name, item, self.items[item])
                logfile.write(f"    Deposited {item} {self.items[item]}\n")
