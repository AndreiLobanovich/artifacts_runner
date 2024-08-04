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


class ProcessingTask(Task):
    def __init__(self, character: TMPCharacter, quantity, location, item):
        super().__init__(character, quantity, location=location, item=item)

    async def __call__(self, client: ArtifactsAPI):
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
        for i in range(self.quantity):
            await client.fight(self.character.name)
            self.progress += 1
            with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
                logfile.write(f'    Killed {self.progress}/{self.quantity}')
        self.progress = 0


class DepositTask(Task):
    def __init__(self, character: TMPCharacter, *items):
        super().__init__(character, 0, location=Locations.BANK)
        self.items = items

    async def __call__(self, client: ArtifactsAPI):
        await super().__call__(client)
        for item in self.items:
            amount = self._get_collected_amount(client, item=item)
            if not amount:
                continue
            await client.deposit_item_in_bank(self.character.name, item, amount)
            with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
                logfile.write(f"    Deposited {amount} {item}\n")
