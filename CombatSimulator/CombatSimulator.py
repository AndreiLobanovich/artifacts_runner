import math
import random

from api.ArtifactsAPI import ArtifactsAPI
from character.Character import Character, ElementalStat, Equipment
from character.item.Item import parse_item


class CombatSimulator:
    def __init__(self, character: str | Character, monster: str | dict):
        self.client: ArtifactsAPI = ArtifactsAPI.instance()
        self.character: 'Character' = Character(character) if isinstance(character, str) else character
        self.monster = self.client.get_monster_by_code(monster) if isinstance(monster, str) else monster
        self.virtual_character = None

    def get_monster_elemental_attacks(self):
        return ElementalStat(
            name="Attack",
            fire=self.monster.get('attack_fire', 0),
            earth=self.monster.get('attack_earth', 0),
            water=self.monster.get('attack_water', 0),
            air=self.monster.get('attack_air', 0)
        )

    def get_monster_elemental_resists(self):
        return ElementalStat(
            name="Resistance",
            fire=self.monster.get('res_fire', 0),
            earth=self.monster.get('res_earth', 0),
            water=self.monster.get('res_water', 0),
            air=self.monster.get('res_air', 0)
        )

    def will_win(self, simulation_count=10, virtual=False):
        combat_results = []
        character = self.virtual_character if virtual else self.character
        for i in range(simulation_count):
            monster_hp = self.monster.get('hp')
            character_hp = character.hp
            characters_turn = True
            turns = 1
            while monster_hp > 0 and character_hp > 0:
                if characters_turn:
                    for attack, damage, enemy_resist in zip(character.attack, character.damage,
                                                            self.get_monster_elemental_resists()):
                        character_damage = attack[1] * (1 + damage[1] * 0.01)
                        damage_reduction = character_damage * enemy_resist[1] * 0.01
                        damage = math.floor(character_damage - damage_reduction)
                        monster_hp -= damage if (lambda: random.random() > enemy_resist[1] / 1000)() else 0
                else:
                    for enemy_attack, resist in zip(self.get_monster_elemental_attacks(), character.resistance):
                        damage_reduction = enemy_attack[1] * resist[1] * 0.01
                        damage = math.ceil(enemy_attack[1] - damage_reduction)
                        character_hp -= damage if (lambda: random.random() > resist[1] / 1000)() else 0
                turns += 1
                characters_turn = not characters_turn
            combat_results.append((turns, character_hp > monster_hp, character_hp, monster_hp))
        avg_turns = sum([result[0] for result in combat_results]) / len(combat_results)
        avg_character_hp = sum([result[2] for result in combat_results]) / len(combat_results)
        avg_monster_hp = sum([result[3] for result in combat_results]) / len(combat_results)
        any_wins = any([result[1] for result in combat_results])
        all_wins = all([result[1] for result in combat_results])
        return {
            "all_wins": all_wins,
            "any_wins": any_wins,
            "avg_turns": avg_turns,
            "character_hp": avg_character_hp,
            "monster_hp": avg_monster_hp
        }

    def get_necessary_equipment(self):
        self.virtual_character = self.character.get_naked_character()
        best_equipment = {}
        winable = False

        for slot in Equipment.__annotations__.keys():
            items = list(map(parse_item, filter(lambda item: slot.replace("_slot", "") == item["type"] and item[
                "level"] <= self.virtual_character.xp.level, self.client.items)))

            item_scores = []

            for item in items:
                self.virtual_character.equip_item(item, virtual=True)
                result = self.will_win(virtual=True)
                if result["any_wins"]:
                    winable = True
                score = (
                        result["any_wins"] * 1000
                        + result["all_wins"] * 10000
                        + (result["monster_hp"] - result["character_hp"])
                        - result["avg_turns"] * 100
                )

                item_scores.append((item, score))
                self.virtual_character.unequip_item(slot)

            sorted_items = sorted(item_scores, key=lambda x: x[1], reverse=True)
            best_equipment[slot] = [item for item, score in sorted_items][::-1]

        return best_equipment, winable
