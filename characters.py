from dataclasses import dataclass


@dataclass
class TMPCharacter:
    name: str
    tools: dict[str, str]
    persistent_inventory: list[str] | None


characters = [
    TMPCharacter(
        "Samriel",
        tools={
            "mining": "iron_pickaxe",
            "woodcutting": "iron_axe"
        },
        persistent_inventory=[
            "steel_axe",
            "forest_whip",
            "battlestaff",
            "skull_staff"
        ]
    ),
    TMPCharacter(
        "Samriella",
        tools={
            "mining": "iron_pickaxe",
            "woodcutting": "iron_axe"
        },
        persistent_inventory=[
            "multislimes_sword"
        ]
    ),
    TMPCharacter(
        "Miriel",
        tools={
            "mining": "iron_pickaxe",
            "woodcutting": "iron_axe",
            "fishing": "spruce_fishing_rod"
        },
        persistent_inventory=[]
    ),
    TMPCharacter(
        "Mitsu",
        tools={
            "woodcutting": "iron_axe"
        },
        persistent_inventory=["skull_staff"]
    ),
    TMPCharacter(
        "Habib",
        tools={
            "mining": "iron_pickaxe"
        },
        persistent_inventory=[
            "steel_axe",
            "forest_whip",
            "battlestaff",
            "skull_staff"
        ]
    )
]
