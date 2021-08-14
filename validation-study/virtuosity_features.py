import glob
import json
import sys

# Add Adorn-o folder to the file path:
sys.path.append("../Adorn-o")

import Adorn_o

print(glob.glob("validation-study/output/*.json"))
song1 = glob.glob("validation-study/output/*.json")[0]

print(Adorn_o.API.get_functions.get_API_from_JSON_file(song1))
# Adorn_o.API.calculate_functions.calculate_rhy_file_for_song()
