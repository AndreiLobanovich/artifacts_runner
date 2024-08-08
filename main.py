import asyncio
import math

from api.ArtifactsAPI import ArtifactsAPI
from character.Tasks import Task, CraftingTask, DepositTask, FightTask, GatherTask
from characters import characters
from utils import clear_logs

a: ArtifactsAPI = ArtifactsAPI.instance()


async def execute_tasks(*tasks: *list[Task], cycles=math.inf):
    i = 0
    while i < cycles:
        for task in tasks:
            await task()
        i += 1


async def main():
    await asyncio.gather(
        execute_tasks(
            FightTask(characters[0], 20, "pig"),
            DepositTask(characters[0]),
            FightTask(characters[0], 20, "skeleton"),
            DepositTask(characters[0])
        ),
        execute_tasks(
            *[CraftingTask(characters[1], 1, item) for item in
              "tromatising_mask steel_legs_armor steel_armor steel_boots steel_helm".split()],
            DepositTask(characters[1])),
        execute_tasks(CraftingTask(characters[2], 5, "cheese"), DepositTask(characters[2])),
        execute_tasks(FightTask(characters[3], 20, "flying_serpent"), DepositTask(characters[3])),
        execute_tasks(FightTask(characters[4], 20, "wolf"), DepositTask(characters[4]))
    )


async def retry_main():
    clear_logs()
    while True:
        if a.server_is_up():
            try:
                await main()
            except Exception as e:
                print(f"Error occurred: {e}. Retrying in 10 seconds...")
                await asyncio.sleep(10)
        else:
            print("Server is down. Waiting for it to come back up...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(retry_main())
