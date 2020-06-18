import requests
import json
import re

import matchers

API_URL = "http://api.pathofexile.com/character-window/"


class AddedDamage:
    def __init__(self, text):
        self.text = text.lower()
        self.min = 0
        self.max = 0
        self.increased = 0
        self.damage_type = "physical"
        self._parse_text()

    def _check_relevant(self):
        a = matchers.add_check.search(self.text)
        b = matchers.damage_increased.search(self.text)
        if not a and not b:
            return False
        if a:
            return "add"
        else:
            return "inc"

    def _parse_text(self):
        direction = self._check_relevant()
        if not direction:
            raise Exception
        if direction == "add":
            self._add_damage()
        else:
            self._increase_damage()

    def _add_damage(self):
        r = matchers.damage_range.search(self.text).group(0)

        if "to" in r:
            self.min = int(r.split(" ")[0])
            self.max = int(r.split(" ")[2])
        damage_type = matchers.damage_type.search(self.text)
        self.damage_type = damage_type.group(0)

    def _increase_damage(self):
        r = matchers.damage_increased.search(self.text).group(0)
        self.increased = int(matchers.damage_percent.search(r).group(0)[:-1])
        damage_type = matchers.damage_type.search(self.text)
        if damage_type == None:
            self.damage_type = "all"
        else:
            self.damage_type = damage_type.group(1)

    def __str__(self):
        return "Add {} to {} {} damage ({})".format(self.min, self.max, self.damage_type, self.text)

class Character:
    def __init__(self, account_name, character_name):
        params = {"character": character_name,
                  "accountName": account_name}
        r = requests.get(API_URL + "get-items", params=params)
        self.items  = r.json()
        params["reqData"] = "1"
        r = requests.get(API_URL + "get-passive-skills", params=params)
        self.passives = r.json()
        self.get_passives()
        self.skill_groups = []
        self.damage_mods = []
        self.primary_damage_types = []
        primary_skill = self._get_skills()
        for tag in primary_skill["properties"][0]["name"].split(","):
            self.primary_damage_types.append(tag.strip().lower())
        for prop in primary_skill["properties"]:
            if prop["name"] == "Effectiveness of Added Damage":
                self.damage_eff = int(prop["values"][0][0][:-1])
        self.primary_skill = primary_skill

    def sum_added(self):
        minmax_dict = {"min": 0, "max": 0}
        add = {}
        for mod in self.damage_mods:
            if mod.damage_type not in add:
                add[mod.damage_type] = minmax_dict.copy()
            add[mod.damage_type]["min"] += mod.min
            add[mod.damage_type]["max"] += mod.max
        return add

    def sum_increased(self):
        add = {}
        for mod in self.damage_mods:
            if mod.damage_type not in add:
                add[mod.damage_type] = 0
            add[mod.damage_type] += mod.increased
        return add



    def get_passives(self):
        for node_id, item in self.passives["skillTreeData"]["nodes"].items():
            if "stats" in item:
                for stat in item["stats"]:
                    try:
                        a = AddedDamage(stat.lower())
                        self.damage_mods.append(a)
                    except:
                        pass

    def _get_skills(self):
        for item in self.items["items"]:
            gems = self._get_gems(item)
            if gems:
                for group in gems:
                    self.skill_groups.append(gems[group])
        max_len = 0
        active_gem = None
        self.damage_mods += self._get_added_damage_items()
        for group in self.skill_groups:
            self.damage_mods += self._get_added_damage_gems(group)
            if len(group) > max_len:
                active_gem = self._get_active_skill(group)
                max_len = len(group)
        if not active_gem:
            return None
        else:
            return active_gem

    def _get_gems(self, item):
        if "socketedItems" not in item:
            return None
        sockets = {}
        for i, socket in enumerate(item["sockets"]):
            sockets[i] = socket["group"]
        groups = {}
        for gem in item["socketedItems"]:
            tags = gem["properties"][0]
            group = sockets[gem["socket"]]
            if group not in groups:
                groups[group] = []
            groups[group].append(gem)
        return groups

    def _get_active_skill(self, group):
        candidates = []
        for gem in group:
            properties = gem["properties"]
            tags = properties[0]["name"].split(",")
            try:
                if gem["support"]:
                    continue
            except:
                print(gem)
            candidates.append(gem)

        if candidates:
            return candidates[0]
        else:
            return []

    def _get_added_damage_gems(self, group):
        mods = []
        for gem in group:
            for mod in gem["explicitMods"]:
                try:
                    a = AddedDamage(mod)
                    mods.append(a)
                except Exception as e:
                    pass
        return mods

    def _get_added_damage_items(self):
        mods = []
        for item in self.items["items"]:
            this_was_a_weapon = False
            if item["inventoryId"] == "Weapon":
                this_was_a_weapon = True
                for prop in item["properties"]:
                    if prop["name"] == "Physical Damage":
                        damage = prop["values"][0][0]
                        mindam = damage.split("-")[0]
                        maxdam = damage.split("-")[1]
                        a = AddedDamage("adds {} to {} physical damage".format(mindam, maxdam))
                        mods.append(a)
            for mod in item["explicitMods"]:
                try:
                    if this_was_a_weapon and "physical damage" in mod.lower():
                        continue
                    a = AddedDamage(mod.lower())
                    mods.append(a)
                except Exception as e:
                    pass
        return mods

    def get_dominant_increase(self):
        add = self.sum_added()
        avg_damage = 0
        damage_type = None
        for t in add:
            avg = (add[t]["max"] + add[t]["min"]) / 2
            if avg > avg_damage:
                damage_type = t
                avg_damage = avg

        avg_damage = avg_damage
        self.primary_damage_types.append(damage_type)

        inc = self.sum_increased()
        total_sum = 0
        for dt in self.primary_damage_types:
            if dt in inc:
                total_sum += inc[dt]
        output = "```"
        output += "Guessed primary skill: {}\n".format(self.primary_skill["typeLine"])
        output += "Average damage {}, increased {}%\n".format(avg_damage, total_sum)
        output += "10 added damage gives {:.2f}% more damage\n".format((((avg_damage + 10) / avg_damage) - 1) * 100)
        output += "10% increased damage give {:.2f}% more damage\n```".format((((total_sum + 10) / total_sum) - 1) * 100)
        return output
                



if __name__ == "__main__":
    c = Character("Rulzern", "Rulzoff")
    print(c.sum_added())
    print(c.sum_increased())
    print(c.get_dominant_increase())
