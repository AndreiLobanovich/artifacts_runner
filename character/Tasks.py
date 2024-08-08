from __future__ import annotations

from abc import ABC

from api.ArtifactsAPI import ArtifactsAPI
from characters import TMPCharacter
from utils import Locations, Slots


class Task(ABC):
    location: Locations | None
    item: str | None
    quantity: int
    monster: dict | None
    client: ArtifactsAPI = ArtifactsAPI.instance()
    character: TMPCharacter

    def __init__(self, character: TMPCharacter, quantity, item=None):
        if item:
            self.location = self.client.get_item_location(item)
        self.item = item
        self.quantity = quantity
        self.character: TMPCharacter = character

    def __init_subclass__(cls, **kwargs):
        orig_init = cls.__init__

        def new_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            print(
                f'[{self.character.name}]'
                f' {self.__class__.__name__} created'
                f' "get" {self.quantity} of {self.item}'
                f' {self.location.name} {self.location.value}'
            )

        cls.__init__ = new_init

    async def __call__(self):
        await self.client.move(self.character.name, *self.location.value)

    def __del__(self):
        print(
            f'[{self.character.name}] | {self.__class__.__name__} | {self.item} | {self.quantity} | {self.location} finished')

    def _get_collected_amount(self, item=None):
        try:
            items = self.client.get_char_inventory(self.character.name)
            collected = next(filter(lambda i: i["code"] == (self.item if not item else item), items))["quantity"]
        except:
            collected = 0
        return collected

    async def _switch_item(self, slot: Slots, item: str):
        already_equipped = self.client.get_characters_data(self.character.name)[slot.value + "_slot"] == item
        if not already_equipped:
            await self.client.unequip(self.character.name, slot=slot)
            await self.client.equip(self.character.name, item, slot=slot)


class GatherTask(Task):
    def __init__(self, character: TMPCharacter, quantity, item):
        super().__init__(character, quantity, item=item)
        self.collected = self._get_collected_amount(item=self.item)
        self.quantity = self.collected + quantity
        self.monster = None

    async def __call__(self):
        await super().__call__()
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            logfile.write(
                f'{self.character.name} starts {self.__class__.__name__} | location: {self.location.name} | item: {self.item}\n')
            while self.collected < self.quantity:
                cell_data = self.client.get_map_cell(self.location)["data"]
                if pillage := cell_data["content"]["type"] == "monster":
                    if not self.monster:
                        self.monster = self.client.get_monster_by_code(cell_data["content"]["code"])
                    await self.equip_best_weapon()
                    result = await self.client.fight(self.character.name)
                    if "497" in str(result):
                        await DepositTask(self.character)()
                        await self.client.move(self.character.name, *self.location.value)
                    try:
                        if result["data"]["fight"]["result"] == "lose":
                            # skipping task
                            return
                    except Exception as e:
                        logfile.write(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!{str(result)}")

                else:
                    if self.character.tools:
                        subtype = self.client.get_item(self.item)["subtype"]
                        tool = self.character.tools.get(subtype)
                        if tool:
                            await self._switch_item(slot=Slots.WEAPON, item=tool)
                    await self.client.gather_resource(self.character.name)
                logfile.write(f'    {"Pillaged" if pillage else "Gathered"} {self.collected}/{self.quantity}\n')
                self.collected = self._get_collected_amount(item=self.item)
            self.collected = 0

    async def equip_best_weapon(self):
        await self._switch_item(Slots.WEAPON, self.choose_best_weapon().get("code"))

    def choose_best_weapon(self):
        all_weapons = list(filter(lambda i: "weapon" in str(i), self.client.items))
        weapon_codes_in_inventory = [weapon["code"] for weapon in self.client.get_char_inventory(self.character.name)]
        weapon_in_inventory = list(filter(lambda w: w["code"] in weapon_codes_in_inventory, all_weapons))
        try:
            equipped_weapon = self.client.get_item(self.client.get_characters_data(self.character.name)["weapon_slot"])
            weapon_in_inventory.append(equipped_weapon)
        except StopIteration:
            pass

        best_weapon = None
        best_effective_damage = 0

        for weapon in weapon_in_inventory:
            total_damage = 0
            for effect in weapon['effects']:
                attack_type = effect['name']
                attack_value = effect['value']
                resistance = self.monster.get(attack_type.replace('attack_', 'res_'), 0)

                damage_reduction = attack_value * (resistance * 0.1)
                effective_damage = attack_value - damage_reduction

                total_damage += max(0, effective_damage)

            if total_damage > best_effective_damage:
                best_effective_damage = total_damage
                best_weapon = weapon
        return best_weapon


class CraftingTask(Task):
    def __init__(
            self,
            character: TMPCharacter,
            quantity,
            item,
    ):
        super().__init__(character, quantity, item=item)
        self.location = self.client.get_item_location(item)

    async def __call__(self):
        # prep for crafting
        recipie = {craft_item["code"]: craft_item["quantity"] for craft_item in self.client.get_item_recipie(self.item)}
        items_to_get_from_bank = dict()
        items_to_get_otherwise = dict()
        for item in recipie:
            if (collected := self._get_collected_amount(item=item)) < (recipie[item] * self.quantity):
                required = recipie[item] * self.quantity - collected
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
            if not self.client.get_item_recipie(item):
                preceding_tasks.append(GatherTask(self.character, items_to_get_otherwise[item], item))
            else:
                preceding_tasks.append(CraftingTask(self.character, items_to_get_otherwise[item], item))
        for preceding_task in preceding_tasks:
            await preceding_task()
        # crafting itself
        await super().__call__()
        response = await self.client.craft(self.character.name, qtt=self.quantity, code=self.item)
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            if "insufficient" in str(response):
                logfile.write(f"    Craft skipped, insufficient resources\n")
            else:
                logfile.write(f"    Crafted {self.quantity} {self.item}\n")


class FightTask(Task):
    progress: int = 0

    def __init__(self, character: TMPCharacter, quantity, monster_code):
        super().__init__(character, quantity)
        self.monster = self.client.get_monster_by_code(monster_code)
        self.location = self.client.get_location_by_monster(monster_code)

    async def __call__(self):
        await super().__call__()
        await self.equip_best_weapon()
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            for i in range(self.quantity):
                result = await self.client.fight(self.character.name)
                if "497" in str(result):
                    await DepositTask(self.character)()
                self.progress += 1
                logfile.write(f'    Killed {self.progress}/{self.quantity}')
        self.progress = 0

    async def equip_best_weapon(self):
        await self._switch_item(Slots.WEAPON, self.choose_best_weapon().get("code"))

    def choose_best_weapon(self):
        all_weapons = list(filter(lambda i: "weapon" in str(i), self.client.items))
        weapon_codes_in_inventory = [weapon["code"] for weapon in self.client.get_char_inventory(self.character.name)]
        weapon_in_inventory = list(filter(lambda w: w["code"] in weapon_codes_in_inventory, all_weapons))
        equipped_weapon = self.client.get_item(self.client.get_characters_data(self.character.name)["weapon_slot"])
        weapon_in_inventory.append(equipped_weapon)

        best_weapon = None
        best_effective_damage = 0

        for weapon in weapon_in_inventory:
            total_damage = 0
            for effect in weapon['effects']:
                attack_type = effect['name']
                attack_value = effect['value']
                resistance = self.monster.get(attack_type.replace('attack_', 'res_'), 0)

                damage_reduction = attack_value * (resistance * 0.1)
                effective_damage = attack_value - damage_reduction

                total_damage += max(0, effective_damage)

            if total_damage > best_effective_damage:
                best_effective_damage = total_damage
                best_weapon = weapon
        return best_weapon


class DepositTask(Task):
    def __init__(self, character: TMPCharacter):
        super().__init__(character, 0)
        self.location = Locations.BANK

    async def __call__(self):
        await super().__call__()
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            inventory_item_codes = [item["code"] for item in self.client.get_char_inventory(self.character.name)]
            for item in inventory_item_codes:
                if item in self.character.persistent_inventory + list(self.character.tools.values()):
                    continue
                amount = self._get_collected_amount(item=item)
                if not amount:
                    continue
                await self.client.deposit_item_in_bank(self.character.name, item, amount)
                logfile.write(f"    Deposited {amount} {item}\n")


class RetrieveFromBankTask(Task):
    def __init__(self, character: TMPCharacter, **items):
        super().__init__(character, 0)
        self.location = Locations.BANK
        self.items = items

    async def __call__(self):
        await super().__call__()
        with open(f"logs/{self.character.name}.log", "a", encoding="utf-8") as logfile:
            for item in self.items:
                await self.client.retrieve_item_from_bank(self.character.name, item, self.items[item])
                logfile.write(f"    Deposited {item} {self.items[item]}\n")
