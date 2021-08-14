
import json


import guitarpro

import parser
import parser.API.dict_conversion as api2dict


gp5_file_dict = "./Adorn-o/gp5files/test_scores/dict_test.gp5"
gp5song_dict = guitarpro.parse(gp5_file_dict)
api_song_dict = parser.API.get_functions.get_song_data(gp5song_dict)


dict_song = api2dict.tracks_to_dict(api_song_dict)

# Write out the JSON:
with open("data_file.json", "w") as write_file:
    json.dump(dict_song, write_file, indent=4, )

# Read in JSON
with open("data_file.json", "r") as read_file:
    data = json.load(read_file)

new_song_api = api2dict.dict_to_tracks(data)

print(new_song_api)

assert new_song_api[0].meta_data == api_song_dict[0].meta_data
assert new_song_api[0].measures[0].meta_data == api_song_dict[0].measures[0].meta_data

for new_m, old_m in zip(new_song_api[0].measures,  api_song_dict[0].measures):

    for new_n, old_n in zip(new_m.notes, old_m.notes):
        assert new_n == old_n

assert new_song_api[0] == api_song_dict[0]
