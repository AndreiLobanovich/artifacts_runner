from abc import ABC

from api.ArtifactsAPI import ArtifactsAPI
from utils import Locations


class Task(ABC):
    location: Locations | None
    item: str | None
    quantity: int

    def __init__(self, quantity, location=None, item=None):
        self.location = location
        self.item = item
        self.quantity = quantity

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        print(f'Starting {self.__class__.__name__} | location: {self.location} | item: {self.item}')
        try:
            await client.move(*self.location.value, character_name)
        except Exception as e:
            print(f"Error during move: {e}")


class GatherTask(Task):
    def __init__(self, quantity, location, item):
        super().__init__(quantity, location=location, item=item)

    def get_collected_amount(self, client: ArtifactsAPI, character_name):
        try:
            items = client.get_char_inventory(character_name)
            collected = next((i["quantity"] for i in items if i["code"] == self.item), 0)
        except Exception as e:
            print(f"Error getting collected amount: {e}")
            collected = 0
        return collected

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        await super().__call__(client, character_name)
        while (collected := self.get_collected_amount(client, character_name)) < self.quantity:
            try:
                await client.gather_resource(character_name)
                print(f'    Gathered {collected}/{self.quantity}')
            except Exception as e:
                print(f"Error during gathering resource: {e}")
                break  # Exit loop on error
        self.progress = 0


class ProcessingTask(Task):
    def __init__(self, quantity, location, item):
        super().__init__(quantity, location=location, item=item)

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        await super().__call__(client, character_name)
        try:
            await client.craft(character_name, qtt=self.quantity, code=self.item)
            print(f"    Crafted {self.quantity} {self.item}")
        except Exception as e:
            print(f"Error during crafting: {e}")


class FightTask(Task):
    progress: int = 0

    def __init__(self, quantity, location):
        super().__init__(quantity, location=location)

    async def __call__(self, client: ArtifactsAPI, character_name: str):
        await super().__call__(client, character_name)
        try:
            for _ in range(self.quantity):
                await client.fight(character_name)
                self.progress += 1
                print(f'    Killed {self.progress}/{self.quantity}')
        except Exception as e:
            print(f"Error during fighting: {e}")
        self.progress = 0