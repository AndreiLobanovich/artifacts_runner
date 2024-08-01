import asyncio
from enum import Enum
from functools import wraps


def task(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print(
            f'    {" ".join((
                func.__name__,
                *list(map(str, args[1:])),
                *([f'{key}: {value}' for key, value in kwargs.items()] if kwargs else [""])
            ))}',
            end=" "
        )
        data = func(*args, **kwargs).json()
        while "error" in data:
            if data["error"]["code"] == 490:
                return
            print("    error. sleep for 1 sec")
            await asyncio.sleep(1)
            data = func(*args, **kwargs).json()
        else:
            sleep_time = data["data"]["cooldown"]["total_seconds"]
            print(f"    Success, napping for {sleep_time} seconds")
            await asyncio.sleep(sleep_time)

    return wrapper


class Slots(Enum):
    WEAPON = "weapon"


class Locations(Enum):
    GEAR_CRAFT_BENCH = (3, 1)
    COPPER_MINE = (2, 0)
    SMELTER = (1, 5)
    WEAPON_CRAFT_BENCH = (2, 1)
    IRON_MINE = (1, 7)
    ASHWOOD_MINE = (-1, 0)
    WOODCUTTING_BENCH = (-2, -3)
    GRUDGEON_FISHING_SPOT = (4, 2)
    COOKING_BENCH = (1, 1)
    CHICKEN_SLAUGHTER_SPOT = (0, 1)
    JEWELERY_CRAFT_BENCH = (1, 3)
