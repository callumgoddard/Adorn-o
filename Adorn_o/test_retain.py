

import shutil
import glob
import os.path
import os
# 3rd party imports
import guitarpro

import cbr
import parser

gp5_file = "./gp5files/Listening-test-mono/tol.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)

database = cbr.Database('test_retain', True)

#shutil.rmtree(database.save_folder + "/output/")
#shutil.rmtree(database.save_folder + "/gpfiles/")

database.load()
assert len(list(database.data.keys())) == 0

output = cbr.retain(
    api_song,
    'tol test',
    database,
    artist_and_title_from_file_name=False,
    add_to_database=False)

database.load()
print(output)
assert os.path.isfile(output)
assert len(list(database.data.keys())) == 0

output = cbr.retain(
    api_song,
    'tol test',
    database,
    artist_and_title_from_file_name=False,
    add_to_database=True)

database.load()
print(output)
assert os.path.isfile(output)
assert len(list(database.data.keys())) == 2

database = cbr.Database('test_retain', True)

for file in glob.glob(database.save_folder + "/output/*"):
    if os.path.isdir(file):
        continue
    os.remove(file)

database.load()
assert len(list(database.data.keys())) == 0

output = cbr.retain(
    api_song, 'tol test', database, artist_and_title_from_file_name=True)

database.load()
assert os.path.isfile(output)
assert list(set([e[1] for e in list(database.data.values())])) == ['EdSheeran']
