from __future__ import division, print_function, absolute_import

# 3rd party imports
import guitarpro

import parser

# Read in the file:
gp5_file = "./gp5files/test_scores/natural_harmonic_pitches.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)
test_song = api_song[0]

harmonics = (test_song.measures[0].notes + test_song.measures[1].notes +
             test_song.measures[2].notes + test_song.measures[3].notes +
             test_song.measures[4].notes + test_song.measures[5].notes)
pitches = (test_song.measures[6].notes + test_song.measures[7].notes +
           test_song.measures[8].notes + test_song.measures[9].notes +
           test_song.measures[10].notes + test_song.measures[11].notes)

for harm, pitch in zip(harmonics, pitches):
    if isinstance(harm, parser.API.datatypes.AdornedNote):
        print("harm pitch:", harm.note.pitch)
        print("harm fret:", harm.note.fret_number)
        harm_interval = parser.utilities.fret_2_harmonic_interval[harm.note.fret_number]
        if harm_interval == 'none':
            harm_interval = 0
        print(harm.note.fret_number, harm.note.string_tuning[harm.note.string_number], harm_interval)
        print(harm.note.string_tuning[harm.note.string_number] + harm_interval)
    if isinstance(pitch, parser.API.datatypes.AdornedNote):
        print("regular pitch", pitch.note.pitch)

print("harmonic intervals:")

for harm, pitch in zip(harmonics, pitches):

    if isinstance(harm, parser.API.datatypes.AdornedNote) and isinstance(pitch, parser.API.datatypes.AdornedNote):
        print(harm.note.fret_number, ":", pitch.note.pitch - harm.note.string_tuning[harm.note.string_number], ",")
