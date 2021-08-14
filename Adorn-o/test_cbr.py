

import glob
import os.path

# 3rd party imports
import guitarpro

import cbr
import parser


test_database = cbr.Database('test_cbr', True)

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


test_database = cbr.Database('test_cbr')
# Read in the file:
gp5_file = "./gp5files/Listening-test-mono/tol.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)
test_song = api_song[0]

complexity_weight = 1
difficulty_weight = 1
similarity_threshold = 95
gp5_wellformedness = True

note_list = parser.API.calculate_functions.calculate_tied_note_durations(
            test_song)
notes_in_measure = parser.API.calculate_functions.calculate_bars_from_note_list(
    note_list, test_song)

new_measures = []
for unadorned_measure in test_song.measures:
    measure_note_index = unadorned_measure.meta_data.number -1
    candidate_set = cbr.retrieval(
        unadorned_measure,
        notes_in_measure[measure_note_index],
        test_database,
        complexity_weight,
        difficulty_weight,
        method='all',
        similarity_threshold=0,
        percentile_range=[0, 100])

    # get only the adorned_measure data:
    adorned_measures = [am.measure for am in candidate_set]

    new_measure = cbr.reuse(unadorned_measure, notes_in_measure[measure_note_index], adorned_measures,
                            complexity_weight, difficulty_weight, 'RD',
                            gp5_wellformedness)
    revised_newly_adorned_measure = cbr.revise(
        new_measure.measure, revise_for_gp5=True)
    new_measures.append(revised_newly_adorned_measure)

new_song = parser.API.datatypes.Song(test_song.meta_data, new_measures)
new_song = cbr.revise(new_song, revise_for_gp5=True)

cbr.retain(
    api_song_data=new_song,
    song_title=new_song.meta_data.title,
    database=test_database,
    artist_and_title_from_file_name=False)

# Read in the file:
gp5_file = "./gp5files/one_note.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)
test_song = api_song[0]

complexity_weight = 1
difficulty_weight = 1
similarity_threshold = 95
gp5_wellformedness = True


note_list = parser.API.calculate_functions.calculate_tied_note_durations(
            test_song)
notes_in_measure = parser.API.calculate_functions.calculate_bars_from_note_list(
    note_list, test_song)

weight_set = 'RD'
new_measures = []
for unadorned_measure in test_song.measures:
    measure_note_index = unadorned_measure.meta_data.number -1
    candidate_set = cbr.retrieval(
        unadorned_measure,
        notes_in_measure[measure_note_index],
        test_database,
        complexity_weight,
        difficulty_weight,
        method='all',
        similarity_threshold=0,
        percentile_range=[0, 100])

    # get only the adorned_measure data:
    adorned_measures = [am.measure for am in candidate_set]

    new_measure = cbr.reuse(unadorned_measure=unadorned_measure, unadorned_measure_notes=notes_in_measure[measure_note_index], adorned_measures=adorned_measures,
                            complexity_weight=complexity_weight, difficulty_weight=difficulty_weight, weight_set=weight_set,
                            gp5_wellformedness=gp5_wellformedness)
    revised_newly_adorned_measure = cbr.revise(
        new_measure.measure, revise_for_gp5=True)
    new_measures.append(revised_newly_adorned_measure)

new_song = parser.API.datatypes.Song(test_song.meta_data, new_measures)
new_song = cbr.revise(new_song, revise_for_gp5=True)

cbr.retain(
    api_song_data=new_song,
    song_title=new_song.meta_data.title,
    database=test_database,
    artist_and_title_from_file_name=False)
