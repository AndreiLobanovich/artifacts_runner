from dataclasses import dataclass
from typing import List


@dataclass
class Effect:
    name: str
    value: int


@dataclass
class RecipiePart:
    code: str
    quantity: int


@dataclass
class Craft:
    skill: str
    level: int
    items: list[RecipiePart]
    quantity: int


@dataclass
class Item:
    name: str
    code: str
    level: int
    type: str
    subtype: str
    description: str
    effects: List[Effect]
    craft: Craft


@dataclass
class GreatExchange:
    code: str
    stock: int
    sell_price: int
    buy_price: int


@dataclass
class Data:
    item: Item
    great_exchange: GreatExchange | None


@dataclass
class Response:
    data: Data


def parse_effects(effects_data):
    return [Effect(**effect) for effect in effects_data]


def parse_craft(craft_data):
    items = [RecipiePart(**item) for item in craft_data['items']]
    return Craft(skill=craft_data['skill'], level=craft_data['level'], items=items, quantity=craft_data['quantity'])


def parse_item(item_data):
    effects = parse_effects(item_data['effects']) if item_data.get('effects') else None
    craft = parse_craft(item_data['craft']) if item_data.get('craft') else None
    return Item(
        name=item_data['code'],
        code=item_data['code'],
        level=item_data['level'],
        type=item_data['type'],
        subtype=item_data.get('subtype', ''),
        description=item_data.get('description', ''),
        effects=effects,
        craft=craft
    )


def parse_great_exchange(ge_data):
    return GreatExchange(**ge_data)


def parse_data(data):
    item = parse_item(data['item'])
    ge = parse_great_exchange(data['ge']) if 'ge' in data else None
    return Data(item=item, great_exchange=ge)


def parse_response(response_dict):
    data = parse_data(response_dict['data'])
    return Response(data=data).data.item
