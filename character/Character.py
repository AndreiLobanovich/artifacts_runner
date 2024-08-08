import asyncio
from collections import defaultdict
from copy import deepcopy

from api.ArtifactsAPI import ArtifactsAPI, MakeshiftLocation
from character.item.Item import Item, parse_item
from utils import skill_names, task


class Inventory:
    max_items: int
    items: list[Item]

    def __init__(self, max_items, items):
        self.max_items = max_items
        self.items = items


class Quest:
    name: str
    progress: int
    total: int
    type: str

    def __init__(self, task_name, task_progress, task_total, task_type):
        self.name = task_name
        self.progress = task_progress
        self.total = task_total
        self.type = task_type

    def __str__(self):
        return f'Do {self.name} [{self.progress}/{self.total}]'


class Equipment:
    weapon_slot: Item | None
    shield_slot: Item | None
    helmet_slot: Item | None
    body_armor_slot: Item | None
    leg_armor_slot: Item | None
    boots_slot: Item | None
    ring1_slot: Item | None
    ring2_slot: Item | None
    amulet_slot: Item | None
    artifact1_slot: Item | None
    artifact2_slot: Item | None
    artifact3_slot: Item | None
    consumable1_slot: Item | None
    consumable1_slot_quantity: Item | None
    consumable2_slot: Item | None
    consumable2_slot_quantity: Item | None

    def __init__(self, empty=False, **slots):
        if empty:
            for slot in self.__annotations__.keys():
                setattr(self, slot, None)
        else:
            for slot, item in slots.items():
                setattr(self, slot, item)

    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith('__'):
                yield attr, getattr(self, attr)


class ElementalStat:
    fire: int
    earth: int
    water: int
    air: int
    name: str

    def __init__(self, name, fire, earth, water, air):
        self.fire: int = fire
        self.earth: int = earth
        self.water: int = water
        self.air: int = air
        self.name: str = name

    def __str__(self):
        return f'{self.name}: <fire {self.fire}> <water {self.water}> <air {self.air}> <earth {self.earth}>'

    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith('__') and attr != 'name':
                yield attr, getattr(self, attr)


class XpMeter:
    xp: int
    max_xp: int
    level: int

    def __init__(self, xp, max_xp, level):
        self.xp = xp
        self.max_xp = max_xp
        self.level = level

    def __str__(self):
        return f'lvl{self.level} [{self.xp}/{self.max_xp}]'


class Skill(XpMeter):
    name: str

    def __init__(self, name, xp, max_xp, level):
        super().__init__(xp, max_xp, level)
        self.name = name

    def __str__(self):
        return f'{self.name}' + self.__class__.__str__(self)


class Character:
    name: str
    skin: str
    level: int
    xp: XpMeter
    skills: list[Skill]
    gold: int
    speed: int
    hp: int
    haste: int
    critical_strike: int
    stamina: int
    attack: ElementalStat
    damage: ElementalStat
    resistance: ElementalStat
    position: MakeshiftLocation
    equipment: Equipment
    quest: Quest

    def __init__(self, name):
        self.client: ArtifactsAPI = ArtifactsAPI.instance()
        data = self.client.get_characters_data(name)
        self.name = data['name']
        self.skin = data['skin']
        self.xp = XpMeter(data['xp'], data['max_xp'], data['level'])
        self.skills = self._parse_skills(data)
        self.gold = data['gold']
        self.speed = data['speed']
        self.hp = data['hp']
        self.haste = data['haste']
        self.critical_strike = data['critical_strike']
        self.stamina = data['stamina']
        self.attack = ElementalStat('Attack', data['attack_fire'], data['attack_earth'], data['attack_water'],
                                    data['attack_air'])
        self.damage = ElementalStat('Damage', data['dmg_fire'], data['dmg_earth'], data['dmg_water'], data['dmg_air'])
        self.resistance = ElementalStat('Resistance', data['res_fire'], data['res_earth'], data['res_water'],
                                        data['res_air'])
        self.position = MakeshiftLocation('Position', (data['x'], data['y']))
        self.equipment = self._parse_equipment(data)
        self.quest = Quest(data['task'], data['task_progress'], data['task_total'], data['task_type'])
        self.inventory = Inventory(data['inventory_max_items'],
                                   [parse_item(self.client.get_item(item['code'])) for item in data['inventory'] if
                                    item['code']])

    @task
    def pick_best_fit_for_location(self):
        pass

    @staticmethod
    def _parse_skills(data):
        skills = []
        for skill_name in skill_names:
            skills.append(
                Skill(skill_name, data[f'{skill_name}_xp'], data[f'{skill_name}_max_xp'], data[f'{skill_name}_level']))
        return skills

    def _parse_equipment(self, data):
        slots = defaultdict(lambda: None)
        for slot in list(Equipment.__annotations__.keys()):
            slots[slot] = parse_item(self.client.get_item(data[slot])) if data[slot] else None
        return Equipment(**slots)

    def get_naked_character(self):
        character = deepcopy(self)
        additional_hp = 0
        for slot, item in character.equipment:
            if item:
                for effect in item.effects:
                    if effect.name == "hp":
                        additional_hp += effect.value
        character.hp -= additional_hp
        character.attack = ElementalStat('attack', 0, 0, 0, 0)
        character.damage = ElementalStat('damage', 0, 0, 0, 0)
        character.resistance = ElementalStat('resistance', 0, 0, 0, 0)
        character.equipment = Equipment(empty=True)
        return character

    def _apply_effects(self, item: Item, apply: bool = True):
        factor = 1 if apply else -1
        for effect in item.effects:
            match effect.name:
                case 'hp':
                    self.hp += effect.value * factor
                case 'haste':
                    self.haste += effect.value * factor
                case 'mining':
                    pass
                case 'fishing':
                    pass
                case 'woodcutting':
                    pass
                case _:
                    elemental_type, element = effect.name.split('_')
                    match elemental_type:
                        case 'res':
                            setattr(self.resistance, element, getattr(self.resistance, element) + effect.value * factor)
                        case 'dmg':
                            setattr(self.damage, element, getattr(self.damage, element) + effect.value * factor)
                        case 'attack':
                            setattr(self.attack, element, getattr(self.attack, element) + effect.value * factor)

    async def _real_equip_item(self, item: Item):
        result = await self.client.equip(self.name, item.code, item.type + '_slot')
        if 'error' not in str(result):
            self._virtual_equip_item(item)
            return True
        return False

    async def _real_unequip_item(self, slot):
        result = await self.client.unequip(self.name, slot)
        if 'error' not in str(result):
            self._virtual_unequip_item(slot)
            return True
        return False

    def _virtual_equip_item(self, item: Item):
        self.client.equip(self.name, item.code)
        setattr(self.equipment, item.type + '_slot', item)
        self._apply_effects(item, apply=True)

    def _virtual_unequip_item(self, slot):
        item = getattr(self.equipment, slot)
        if item:
            self._apply_effects(item, apply=False)

    def equip_item(self, item: Item, virtual=True):
        if virtual:
            self._virtual_equip_item(item)
            return True
        else:
            return asyncio.run(self._real_equip_item(item))

    def unequip_item(self, slot, virtual=True):
        if virtual:
            self._virtual_unequip_item(slot)
            return True
        else:
            return asyncio.run(self._real_unequip_item(slot))

    def __str__(self):
        return f'{self.name} {self.xp}'
