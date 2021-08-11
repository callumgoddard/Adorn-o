from __future__ import division, print_function, absolute_import

import os.path
import os

# 3rd party imports
import guitarpro

import cbr
import parser

test_database = cbr.Database('test_database', True)

test_database.add_entries_from_list_of_gp5_files(
    [
        "./gp5files/Listening-test-mono/c.gp5",
        "./gp5files/Listening-test-mono/r.gp5",
        "./gp5files/Listening-test-mono/h-official.gp5",
        "./gp5files/Listening-test-mono/tol.gp5",
        "./gp5files/Listening-test-mono/sd.gp5",
        "./gp5files/Listening-test-mono/s.gp5",
        "./gp5files/Listening-test-mono/wdytiw.gp5"
    ],
    move_tabs=False,
    artist_and_title_from_file_name=False)

# Read in the file:
gp5_file = "./gp5files/Listening-test-mono/tol.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)
test_song = api_song[0]

test_database.load()
assert len(test_database.data.keys()) == 23

data = test_database.load_data_as_lists()
sorted_data = test_database.sort(
    complexity_weight=0, difficulty_weight=0, save=False)
# check there are no duplicate entries added:
data_file_ids = map(lambda d: d[0], data[1:])
sorted_file_ids = map(lambda d: d[0], sorted_data)

assert data_file_ids == sorted_file_ids
assert len(sorted_file_ids) == len(set(sorted_file_ids))

sorted_data = test_database.sort(
    complexity_weight=1, difficulty_weight=1, save=True)
assert len(sorted_file_ids) == len(set(sorted_file_ids))

# reload the database:
test_database.load()
assert len(test_database.data.keys()) == 23

test_database.add_entries_from_gp5_file(
    "./gp5files/one_note.gp5",
    move_tabs=False,
    remove_duplicates=True,
    save_feature_files=False,
    artist_and_title_from_file_name=False)

# reload the database:
test_database.load()
assert len(test_database.data.keys()) == 23 + 4

# Read in the file:
gp5_file = "./gp5files/one_note.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)
test_song = api_song[0]

test_song_tied_note_list = parser.API.calculate_functions.calculate_tied_note_durations(
    test_song)
test_song_notes_in_bar = parser.API.calculate_functions.calculate_bars_from_note_list(
    test_song_tied_note_list, test_song)

measure_id, features = test_database.get_similarity_features_for_measure(
    test_song.measures[0])

single_measure_match = test_database.find_most_similar(test_song.measures[0])

assert test_database.retrieve_entry_data(
    single_measure_match[0]) == parser.API.datatypes.Measure(
        meta_data=test_song.measures[0].meta_data,
        start_time=test_song.measures[0].start_time,
        notes=test_song_notes_in_bar[0])

print("virtuosity_threshold:")
test_database.virtuosity_threshold(
    measure=test_song.measures[0],
    complexity_weight=1,
    difficulty_weight=1,
    similarity_threshold=0)

test_database.virtuosity_threshold(
    complexity_weight=1, difficulty_weight=1, similarity_threshold=0)

test_database.sorted = cbr.database.sorted(None, None, None)
test_database.sort()
assert os.path.isfile(test_database.save_folder + "/" + "sorted.txt")

test_database = cbr.Database('test_database')
assert test_database.sorted.adorned
assert test_database.sorted.complexity_weight == 1
assert test_database.sorted.difficulty_weight == 1

# Test two note retrieval:
gp5_file = "./gp5files/test_scores/two_note_db_test.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)
test_song = api_song[0]

test_database.add_entries_from_gp5_file(
    gp5_file,
    convert_to_json=False,
    move_tabs=False,
    remove_duplicates=True,
    save_feature_files=False,
    artist_and_title_from_file_name=False)

test_database.load()
assert len(test_database.data.keys()) == 23 + 4 + 1

most_sim = test_database.find_most_similar(test_song.measures[0])
sorted_most_sim = test_database.sort_candidate_set(
    most_sim, complexity_weight=1, difficulty_weight=1)

assert test_database.data[sorted_most_sim[0].id][
    0] == './gp5files/test_scores/two_note_db_test.gp5'

if os.path.isfile(test_database.save_folder + "/" + "sorted.txt"):
    os.remove(test_database.save_folder + "/" + "sorted.txt")

retrieved_true = test_database.retrieve_data_from_multiple_entries(
    test_database.data.keys(), True)
retrieved_false = test_database.retrieve_data_from_multiple_entries(
    test_database.data.keys(), False)

assert len(retrieved_true) == len(test_database.data.keys())
assert len(retrieved_false) == len(test_database.data.keys())

for r_t, r_f in zip(retrieved_true, retrieved_false):
    assert r_t[0] in test_database.data.keys()
    assert isinstance(r_t[1], parser.API.datatypes.Measure)
    assert isinstance(r_t, cbr.database.retieved)
    assert isinstance(r_f, parser.API.datatypes.Measure)

json_test_database = cbr.Database('test_database_json', True)

json_test_database.add_entries_from_list_of_json_files(
    [
        "./test_database/json/c.json", "./test_database/json/r.json",
        "./test_database/json/h-official.json",
        "./test_database/json/tol.json", "./test_database/json/sd.json",
        "./test_database/json/s.json", "./test_database/json/wdytiw.json"
    ],
    move_tabs=True,
    artist_and_title_from_file_name=False)

json_test_database.load()
assert len(json_test_database.data.keys()) == 23
for fname in [
        "./test_database_json/json/c.json", "./test_database_json/json/r.json",
        "./test_database_json/json/h-official.json",
        "./test_database_json/json/tol.json",
        "./test_database_json/json/sd.json",
        "./test_database_json/json/s.json",
        "./test_database_json/json/wdytiw.json"
]:
    os.remove(fname)
