from abc import ABC

from api.ArtifactsAPI import ArtifactsAPI
from utils import Locations


class Task(ABC):
    location: Locations | None
    item: str | None
    quantity: int

    def _get_collected_amount(self, client: ArtifactsAPI, character_name, item=None):
        try:
            items = client.get_char_inventory(character_name)
            collected = next(filter(lambda i: i["code"] == self.item if not item else item, items))["quantity"]
        except:
            collected = 0
        return collected

    def __init__(self, quantity, location=None, item=None):
        self.location = location
        self.item = item
        self.quantity = quantity

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        with open(f"logs/{character_name}.log", "a", encoding="utf-8") as logfile:
            logfile.write(
                f'{character_name} starts {self.__class__.__name__} | location: {self.location} | item: {self.item}\n')
        await client.move(character_name, *self.location.value)


class GatherTask(Task):
    def __init__(self, quantity, location, item):
        super().__init__(quantity, location=location, item=item)

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        await super().__call__(client, character_name)
        while (collected := self._get_collected_amount(client, character_name)) < self.quantity:
            await client.gather_resource(character_name)
            with open(f"logs/{character_name}.log", "a", encoding="utf-8") as logfile:
                logfile.write(f'    Gathered {collected}/{self.quantity}\n')
        self.progress = 0


class ProcessingTask(Task):
    def __init__(self, quantity, location, item):
        super().__init__(quantity, location=location, item=item)

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        await super().__call__(client, character_name)
        await client.craft(character_name, qtt=self.quantity, code=self.item)
        with open(f"logs/{character_name}.log", "a", encoding="utf-8") as logfile:
            logfile.write(f"    Crafted {self.quantity} {self.item}\n")


class FightTask(Task):
    progress: int = 0

    def __init__(self, quantity, location):
        super().__init__(quantity, location=location)

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        await super().__call__(client, character_name)
        for i in range(self.quantity):
            await client.fight(character_name)
            self.progress += 1
            with open(f"logs/{character_name}.log", "a", encoding="utf-8") as logfile:
                logfile.write(f'    Killed {self.progress}/{self.quantity}')
        self.progress = 0


class DepositTask(Task):
    def __init__(self, *items):
        super().__init__(0, location=Locations.BANK)
        self.items = items

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        await super().__call__(client, character_name)
        for item in self.items:
            amount = self._get_collected_amount(client, character_name, item=item)
            if not amount:
                continue
            print(await client.deposit_item_in_bank(character_name, item, amount))
            with open(f"logs/{character_name}.log", "a", encoding="utf-8") as logfile:
                logfile.write(f"    Deposited {amount} {item}")
