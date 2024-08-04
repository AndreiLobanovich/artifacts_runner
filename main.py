import asyncio
import math

from api.ArtifactsAPI import ArtifactsAPI
from character.Tasks import Task, GatherTask, ProcessingTask, FightTask, DepositTask, TMPCharacter
from utils import Locations, clear_logs

a: ArtifactsAPI = ArtifactsAPI.instance()

characters = [
    TMPCharacter("Samriel", weapon="multislimes_sword", tool="iron_pickaxe"),
    TMPCharacter("Samriella", weapon="iron_sword", tool="iron_axe"),
    TMPCharacter("Miriel", weapon="water_bow", tool="spruce_fishing_rod"),
    TMPCharacter("Mitsu", weapon="", tool=""),
    TMPCharacter("Habib", weapon="iron_sword", tool="iron_pickaxe")
]


async def execute_tasks(*tasks: *list[Task], cycles=math.inf):
    i = 0
    while i < cycles:
        for task in tasks:
            await task(a)
        i += 1


async def main():
    clear_logs()
    await asyncio.gather(
        execute_tasks(
            GatherTask(characters[0], 116, Locations.IRON_MINE, "iron_ore"),
            ProcessingTask(characters[0], 17, Locations.SMELTER_BENCH, "iron"),
            ProcessingTask(characters[0], 2, Locations.WEAPON_CRAFT_BENCH, "iron_sword"),
            DepositTask(characters[0], "iron_sword", "iron", "iron_ore")

        ),
        execute_tasks(
            GatherTask(characters[1], 36, Locations.SPRUCE_MINE, "spruce_wood"),
            GatherTask(characters[1], 4, Locations.RED_SLIME_SLAUGHTER_SPOT, "red_slimeball", pillage=True),
            GatherTask(characters[1], 4, Locations.GREEN_SLIME_SLAUGHTER_SPOT, "green_slimeball", pillage=True),
            GatherTask(characters[1], 4, Locations.YELLOW_SLIME_SLAUGHTER_SPOT, "yellow_slimeball", pillage=True),
            GatherTask(characters[1], 4, Locations.BLUE_SLIME_SLAUGHTER_SPOT, "blue_slimeball", pillage=True),
            ProcessingTask(characters[1], 6, Locations.WOODCUTTING_BENCH, "spruce_plank"),
            ProcessingTask(characters[1], 1, Locations.GEAR_CRAFT_BENCH, "slime_shield"),
            DepositTask(characters[1], "slime_shield", "spruce_plank")
        ),
        execute_tasks(
            GatherTask(characters[2], 50, Locations.TROUT_FISHING_SPOT, "trout"),
            ProcessingTask(characters[2], 50, Locations.COOKING_BENCH, "cooked_trout"),
            DepositTask(characters[2], "fried_eggs", "egg", "feather", "golden_egg", "raw_chicken", "cooked_trout",
                        "trout")

            # GatherTask(characters[2], 50, Locations.BASS_FISHING_SPOT, "bass"),
            # ProcessingTask(characters[2], 50, Locations.COOKING_BENCH, "cooked_bass"),
            # DepositTask(characters[2], *"trout cooked_bass shrimp".split())

            # GatherTask(5, Locations.SHRIMP_FISHING_SPOT, "shrimp"),
            # ProcessingTask(5, Locations.COOKING_BENCH, "cooked_shrimp"),
            # DepositTask("cooked_shrimp")
        ),
        execute_tasks(
            FightTask(characters[3], 20, Locations.WOLF_SLAUGHTER_SPOT),
            DepositTask(characters[3], "raw_wolf_meat", "wolf_bone", "wolf_hair")
        ),
        execute_tasks(
            GatherTask(characters[4], 72, Locations.IRON_MINE, "iron_ore"),
            ProcessingTask(characters[4], 12, Locations.SMELTER_BENCH, "iron"),
            ProcessingTask(characters[4], 2, Locations.JEWELERY_CRAFT_BENCH, "iron_ring"),
            DepositTask(characters[4], "iron_ring", "iron", "iron_ore")
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
