import json
import glob
import os

game_json_path = os.path.join(os.getcwd(), 'DB', '*.json')

json_files = glob.glob(game_json_path)

merged_data = []

for file in json_files:
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        merged_data.extend(data)

unique_data = {json.dumps(item, sort_keys=True, ensure_ascii=False): item for item in merged_data}.values()

with open('All_PlayStation_Games.json', 'w', encoding='utf-8') as outfile:
    json.dump(list(unique_data), outfile, indent=4, ensure_ascii=False)
