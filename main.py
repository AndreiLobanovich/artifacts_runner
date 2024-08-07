import asyncio
import math
from datetime import datetime

from api.ArtifactsAPI import ArtifactsAPI
from character.Tasks import Task, CraftingTask, FightTask, DepositTask, TMPCharacter
from utils import Locations

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
            await task()
            # Log completion time
            log_file_name = f"logs/{task.character.name}.log"
            with open(log_file_name, "a", encoding="utf-8") as logfile:
                logfile.write(f"Task {task.__class__.__name__} completed at {datetime.now()}\n")
        i += 1

async def main():
    await asyncio.gather(
        execute_tasks(
            CraftingTask(
                characters[0],
                2,
                Locations.WEAPON_CRAFT_BENCH,
                "iron_sword",
            ),
            DepositTask(characters[0], "iron", "iron_sword")
        ),
        execute_tasks(
            CraftingTask(
                characters[1],
                1,
                Locations.GEAR_CRAFT_BENCH,
                "slime_shield",
            ),
            DepositTask(characters[1], "slime_shield")
        ),
        execute_tasks(
            CraftingTask(
                characters[2],
                50,
                Locations.COOKING_BENCH,
                "cooked_trout",
            ),
            DepositTask(
                characters[2],
                "fried_eggs",
                "egg",
                "feather",
                "golden_egg",
                "raw_chicken",
                "cooked_trout",
                "trout"
            )

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
            CraftingTask(
                characters[4],
                2,
                Locations.JEWELERY_CRAFT_BENCH,
                "iron_ring",
            ),
            DepositTask(characters[4], "iron_ring", "iron", "iron_ore")
        ),
    )

async def retry_main():
    while True:
        if a.server_is_up():
            try:
                await main()
            except Exception as e:
                print(f"Error occurred: {e}. Retrying in 10 seconds...")
                raise e
                await asyncio.sleep(10)
        else:
            print("Server is down. Waiting for it to come back up...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(retry_main())
