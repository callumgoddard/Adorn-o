from __future__ import division, print_function, absolute_import

import os

import rpy2.robjects as robjects

import guitarpro

from parser.API.get_functions import get_song_data
import parser.utilities as utilities
import parser.API.calculate_functions as calculate
import feature_analysis
from parser.API.datatypes import Measure

# Read in the GP5 Test file:
gp5_file = "./gp5files/test_scores/fantastic_test.gp5"
gp5song = guitarpro.parse(gp5_file)
api_test_song = get_song_data(gp5song)

test_song = api_test_song[0]

note_list = calculate.calculate_tied_note_durations(test_song)

measure_note_lists = calculate.calculate_bars_from_note_list(
    note_list, test_song)

for measure in test_song.measures:
    note_list_index = measure.meta_data.number - 1
    calculate.calculate_midi_file_for_measure_note_list
    print(note_list_index)

    tied_note_measures = []
    if measure_note_lists[note_list_index] != []:
        for extra_measure in test_song.measures:
            if (extra_measure.start_time < calculate.calculate_note_endtime(
                    measure_note_lists[note_list_index][-1])
                    and extra_measure.start_time >
                    measure_note_lists[note_list_index][-1].note.start_time):
                tied_note_measures.append(extra_measure)

    print(len([measure] + tied_note_measures))

    midi_file = calculate.calculate_midi_file_for_measure_note_list(
        measure_note_lists[note_list_index], [measure] + tied_note_measures,
        'measure')
    mcvs = utilities.run_melconv(midi_file, 'mcsvtest')

    print(midi_file, mcvs)
    print(mcvs.split('./')[-1])
    print(os.getcwd() + '/' + mcvs.split('./')[-1])

    feature_analysis.fantastic_interface.load()
    working_directory = os.getcwd()
    robjects.r['setwd'](working_directory)

    print("measure.number:", measure.meta_data.number)
    try:
        print(feature_analysis.fantastic_interface.compute_features(
            ['measure.csv']))

        os.remove('measure.mid')
        os.remove('measure.csv')
    except:
        continue
"""
Things to test:
    - get a midi test case?
    - get a way of tracking a note over multiple measures
        - just find the end time? and add in the measures that have a
        start time that starts before the note ends, but not after.
        - update the midi function to accept measure lists
    - FANTASTIC:
        - then intergrate it into my system.
            - chunking
            - database building
            - retrieval

"""

measure_note_list = measure_note_lists[1]
print(measure_note_list)

#calculate.calculate_midi_file_for_measure_note_list(measure_note_list,
#                                              measure,
#                                              midi_file_name='measure.mid',
#                                              output_folder=os.getcwd()):

note1 = measure_note_lists[1][0]
note2 = measure_note_lists[1][1]
print(test_song.measures[1].meta_data.tempo)
print(calculate.calculate_FANTASTIC_features_for_note_pair(
    note1, note2, test_song.measures[1]))

note1 = measure_note_lists[1][1]
note2 = measure_note_lists[1][2]
print(calculate.calculate_FANTASTIC_features_for_note_pair(
    note1, note2, test_song.measures[1]))

unadorned_chunk = [note1, note2]
unadorned_measure = test_song.measures[1]
# get the unadorned features:
unadorned_chunk_FANTASTIC_features = calculate.calculate_FANTASTIC_features_for_note_pair(
    unadorned_chunk[0], unadorned_chunk[1], unadorned_measure)

rhy_measure = Measure(unadorned_measure.meta_data,
                      unadorned_measure.start_time, unadorned_chunk)
chunk_rhy = calculate.calculate_rhy_file_for_measure(
    rhy_measure, rhy_file_name="unadorned_chunk.rhy")

unadorned_chunk_SynPy_features = feature_analysis.synpy_interface.compute_features(
    chunk_rhy)

print(unadorned_chunk_FANTASTIC_features)
print(unadorned_chunk_SynPy_features)


# Clear files:
if os.path.isfile(chunk_rhy):
    os.remove(chunk_rhy)

if os.path.isfile('feature_computation.txt'):
    os.remove('feature_computation.txt')

if os.path.isfile('measure.mid'):
    os.remove('measure.mid')


