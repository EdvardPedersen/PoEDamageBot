import re

damage_range = re.compile(r'(\d+ to \d+|\d+)')
damage_type = re.compile(r'(attack|spell|elemental|physical|cold|lightning|fire|chaos)')
add_check = re.compile(r'(added|adds|add)')
increased_check = re.compile(r'(increased)')
damage_increased = re.compile(r'\d+%\ increased ([a-z]*\ damage|damage)')
damage_percent = re.compile(r'\d+%')
