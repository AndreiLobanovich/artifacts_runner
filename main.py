import asyncio
import functools
import math
import random

from api.ArtifactsAPI import ArtifactsAPI
from character.Tasks import Task, GatherTask, ProcessingTask, FightTask
from utils import Locations

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
    await asyncio.gather(
        execute_tasks(
            char_names[0],
            GatherTask(108, Locations.IRON_MINE, "iron_ore"),
            ProcessingTask(18, Locations.SMELTER, "iron"),
        ),
        execute_tasks(
            char_names[1],
            GatherTask(36, Locations.ASHWOOD_MINE, "ash_wood"),
            ProcessingTask(6, Locations.WOODCUTTING_BENCH, "ash_plank"),
            ProcessingTask(2, Locations.GEAR_CRAFT_BENCH, "wooden_shield")
        ),
        execute_tasks(
            char_names[2],
            GatherTask(5, Locations.GRUDGEON_FISHING_SPOT, "gudgeon"),
            ProcessingTask(5, Locations.COOKING_BENCH, "cooked_gudgeon"),
        ),
        execute_tasks(
            char_names[3],
            FightTask(1, Locations.CHICKEN_SLAUGHTER_SPOT)
        ),
        execute_tasks(
            char_names[4],
            GatherTask(24, Locations.COPPER_MINE, "copper_ore"),
            ProcessingTask(4, Locations.SMELTER, "copper"),
            ProcessingTask(1, Locations.GEAR_CRAFT_BENCH, "copper_ring")
        ),
    )

asyncio.run(main())
