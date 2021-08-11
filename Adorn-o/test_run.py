from __future__ import division, print_function, absolute_import

import glob
from collections import namedtuple

# 3rd party imports
import guitarpro

import cbr
import parser

database = cbr.Database('test_run', True)

database.add_entries_from_list_of_gp5_files(
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
database.sort(complexity_weight=1, difficulty_weight=1)

# Read in the GP5 Test file:
gp5_file = "./gp5files/Listening-test-mono/tol.gp5"
gp5song = guitarpro.parse(gp5_file)
api_test_song = parser.API.get_functions.get_song_data(gp5song)

test_song = api_test_song[0]



best_m, loop, loop_wni = cbr.run_module.action_reflection_loop(
    database,
    unadorned_measure=api_test_song[0].measures[0],
    virtuosity_thresh=cbr.database.VirtuosityThreshold(1000, 1000, []),
    notes_in_measure=parser.API.calculate_functions.calculate_tied_note_durations(api_test_song[0].measures[0]),
    complexity_weight=1,
    difficulty_weight=1,
    reflection_loop_limit=None,
    no_improvement_limit=None,
    similarity_threshold_relax_increment=101,
    percentile_range_relax_increment=0,
    similarity_threshold_limit=0,
    percentile_limit=0)

assert loop == 1

best_m, loop, loop_wni = cbr.run_module.action_reflection_loop(
    database,
    unadorned_measure=api_test_song[0].measures[0],
    virtuosity_thresh=cbr.database.VirtuosityThreshold(1000, 1000, []),
    notes_in_measure=parser.API.calculate_functions.calculate_tied_note_durations(api_test_song[0].measures[0]),
    complexity_weight=1,
    difficulty_weight=1,
    reflection_loop_limit=None,
    no_improvement_limit=None,
    similarity_threshold_relax_increment=0,
    percentile_range_relax_increment=100,
    similarity_threshold_limit=0,
    percentile_limit=0)

assert loop == 1

best_m, loop, loop_wni = cbr.run_module.action_reflection_loop(
    database,
    unadorned_measure=api_test_song[0].measures[0],
    virtuosity_thresh=cbr.database.VirtuosityThreshold(1000, 1000, []),
    notes_in_measure=parser.API.calculate_functions.calculate_tied_note_durations(api_test_song[0].measures[0]),
    complexity_weight=1,
    difficulty_weight=1,
    reflection_loop_limit=None,
    no_improvement_limit=None,
    similarity_threshold_relax_increment=0,
    percentile_range_relax_increment=50,
    similarity_threshold_limit=0,
    percentile_limit=0,
    percentile_range=[50, 100])

assert loop == 2

best_m, loop, loop_wni = cbr.run_module.action_reflection_loop(
    database,
    unadorned_measure=api_test_song[0].measures[0],
    virtuosity_thresh=cbr.database.VirtuosityThreshold(0, 0, []),
    notes_in_measure=[],
    complexity_weight=1,
    difficulty_weight=1,
    no_improvement_limit=None,
    similarity_threshold_relax_increment=0,
    percentile_range_relax_increment=0,
    similarity_threshold_limit=0,
    percentile_limit=0,
    percentile_range=[0, 100])

assert loop == 0

unadorned_measure = api_test_song[0].measures[0]
virtuosity_percentile = 99
virtuosity_similarity_threshold = 0
measures_virtuosity_thresh = database.virtuosity_threshold(
    complexity_weight=1,
    difficulty_weight=1,
    measure=unadorned_measure,
    virtuosity_percentile=virtuosity_percentile,
    similarity_threshold=virtuosity_similarity_threshold)

best_m, loop, loop_wni = cbr.run_module.action_reflection_loop(
    database,
    unadorned_measure=api_test_song[0].measures[0],
    virtuosity_thresh=measures_virtuosity_thresh,
    notes_in_measure=[],
    complexity_weight=1,
    difficulty_weight=1,
    reflection_loop_limit=None,
    similarity_threshold_relax_increment=50,
    percentile_range_relax_increment=0,
    similarity_threshold_limit=0,
    percentile_limit=0,
    percentile_range=[0, 100])

assert loop == 3

cbr.run_action_reflection(gp5_file,
                          database,
                          complexity_weight=1,
                          difficulty_weight=1,
                          artist_and_title_from_file_name=False,
                          gp5_wellformedness=True,
                          add_to_database=True,
                          virtuosity_percentile=99,
                          virtuosity_similarity_threshold=0,
                          reflection_loop_limit=None,
                          similarity_threshold_relax_increment=20,
                          percentile_range_relax_increment=0,
                          similarity_threshold_limit=0,
                          percentile_limit=0)

cbr.run(gp5_file,
        database,
        complexity_weight=1,
        difficulty_weight=1,
        artist_and_title_from_file_name=False,
        gp5_wellformedness=True,
        add_to_database=False,
        similarity_threshold=0)
