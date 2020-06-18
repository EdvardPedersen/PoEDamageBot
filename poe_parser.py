import requests
import json

params_items = {"character": "Rulzcocnova",
                "accountName": "Rulzern"}

r = requests.get("http://api.pathofexile.com/character-window/get-items", params=params_items)
dict_items = r.json()
for item in dict_items["items"]:
    print(item["name"])
    if "explicitMods" in item:
        for i in item["explicitMods"]:
            if "cold damage" in i.lower():
                print(i)
    if "properties" in item:
        print(item["properties"])
