import asyncio
import functools
import math
import random

from api.ArtifactsAPI import ArtifactsAPI
from character.Tasks import Task, GatherTask, ProcessingTask, FightTask, DepositTask
from utils import Locations, clear_logs

var = functools.partial

a = ArtifactsAPI()
char_names = [
    "Samriel",
    "Samriella",
    "Miriel",
    "Mitsu",
    "Habib"
]


async def execute_tasks(char_name, *tasks: *list[Task], cycles=math.inf):
    i = 0
    while i < cycles:
        for task in tasks:
            await task(a, char_name)
        i += 1


async def main():
    clear_logs()
    await asyncio.gather(
        execute_tasks(
            char_names[0],
            FightTask(324, Locations.MUSHMUSH_SLAUGHTER_SPOT),
            cycles=1
        ),
        execute_tasks(
            char_names[1],
            GatherTask(36, Locations.ASHWOOD_MINE, "ash_wood"),
            ProcessingTask(6, Locations.WOODCUTTING_BENCH, "ash_plank"),
            ProcessingTask(2, Locations.GEAR_CRAFT_BENCH, "wooden_shield"),
            DepositTask("wooden_shield")
        ),
        execute_tasks(
            char_names[2],
            GatherTask(5, Locations.GRUDGEON_FISHING_SPOT, "gudgeon"),
            ProcessingTask(5, Locations.COOKING_BENCH, "cooked_gudgeon"),
            DepositTask("cooked_gudgeon")
        ),
        execute_tasks(
            char_names[3],
            FightTask(10, Locations.CHICKEN_SLAUGHTER_SPOT),
            DepositTask("feather", "raw_chicken", "egg")
        ),
        execute_tasks(
            char_names[4],
            GatherTask(30, Locations.COPPER_MINE, "copper_ore"),
            ProcessingTask(5, Locations.SMELTER, "copper"),
            ProcessingTask(1, Locations.JEWELERY_CRAFT_BENCH, "copper_ring"),
            DepositTask("copper_ring", "copper", "copper_ore")
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
