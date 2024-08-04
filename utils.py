import asyncio
import os
import sys
from enum import Enum
from functools import wraps


def task(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with open(f"logs/{args[1]}.log", "a", encoding="utf-8") as logfile:
            logfile.write(
                f'    {" ".join((
                    func.__name__,
                    *list(map(str, args[1:])),
                    *([f'{key}: {value}' for key, value in kwargs.items()] if kwargs else [""])
                ))}'
            )
            data = func(*args, **kwargs).json()
            while "error" in data:
                err_code = data["error"]["code"]
                match err_code:
                    case 490:
                        f"    {args[1]} already on the spot"
                        return
                    case 499:
                        time_to_sleep = int("".join(ch for ch in data["error"]["message"] if ch.isnumeric()))
                        logfile.write(f"    {args[1]} in calldown, napping for {time_to_sleep} seconds\n")
                        await asyncio.sleep(time_to_sleep)
                    case 478:
                        logfile.write(f"    {args[1]} !!!! insufficient resources for craft\n")
                        return data
                    case _:
                        logfile.write(str(data) + '\n')
                        return
                data = func(*args, **kwargs).json()
            else:
                sleep_time = data["data"]["cooldown"]["total_seconds"]
                logfile.write(f"    Success, {args[1]} is napping for {sleep_time} seconds\n")
                await asyncio.sleep(sleep_time)
        return data

    return wrapper


class Slots(Enum):
    WEAPON = "weapon"
    RING_1 = "ring1"
    RING_2 = "ring2"


class Locations(Enum):
    GEAR_CRAFT_BENCH = (3, 1)
    WEAPON_CRAFT_BENCH = (2, 1)
    WOODCUTTING_BENCH = (-2, -3)
    SMELTER_BENCH = (1, 5)
    COOKING_BENCH = (1, 1)
    JEWELERY_CRAFT_BENCH = (1, 3)

    COPPER_MINE = (2, 0)
    IRON_MINE = (1, 7)
    ASHWOOD_MINE = (6, 1)
    SPRUCE_MINE = (-2, 5)
    GOLD_MINE = (10, -4)
    DEADTREE_MINE = (9, 8)
    BIRCHTREE_MINE = (3, 5)
    COAL_MINE = (1, 6)

    GUDGEON_FISHING_SPOT = (4, 2)
    SHRIMP_FISHING_SPOT = (5, 2)
    TROUT_FISHING_SPOT = (-2, 6)
    BASS_FISHING_SPOT = (-3, 6)

    CHICKEN_SLAUGHTER_SPOT = (0, 1)
    COW_SLAUGHTER_SPOT = (0, 2)
    MUSHMUSH_SLAUGHTER_SPOT = (5, 3)
    FLYING_SERPENT_SLAUGHTER_SPOT = (5, 4)
    GREEN_SLIME_SLAUGHTER_SPOT = (0, -1)
    RED_SLIME_SLAUGHTER_SPOT = (1, -1)
    YELLOW_SLIME_SLAUGHTER_SPOT = (1, -2)
    BLUE_SLIME_SLAUGHTER_SPOT = (2, -1)
    SKELETON_SLAUGHTER_SPOT = (8, 6)
    WOLF_SLAUGHTER_SPOT = (-2, 1)
    OGRE_SLAUGHTER_SPOT = (-5, -4)

    BANK = (4, 1)


skill_to_location = {
    "gearcrafting": Locations.GEAR_CRAFT_BENCH,
    "weaponcrafting": Locations.WEAPON_CRAFT_BENCH,
    "mining": Locations.SMELTER_BENCH,
    "woodcutting": Locations.WOODCUTTING_BENCH,
    "cooking": Locations.COOKING_BENCH,
    "jewelrycrafting": Locations.JEWELERY_CRAFT_BENCH
}


def clear_logs():
    logs_dir = "./logs"
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            file_path = os.path.join(logs_dir, filename)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f'Could not remove {file_path}. Error: {e}')
                sys.exit()
    else:
        print(f'Directory {logs_dir} does not exist')
        sys.exit()
