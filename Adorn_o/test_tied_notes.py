

from fractions import Fraction

import guitarpro
import parser

gpfile = guitarpro.parse("./database/input/testing/test.gp5")

api_song = parser.API.get_functions.get_song_data(gpfile)

tied_notes = parser.API.calculate_functions.calculate_tied_note_durations(
    api_song[0])

assert tied_notes[-1].note.duration == Fraction(9, 8)
assert tied_notes[-2].note.duration == Fraction(3, 16)

notes_in_bars = parser.API.calculate_functions.calculate_bars_from_note_list(
    tied_notes, api_song[0])

new_song_new_measures = []
for measure in api_song[0].measures:
    m_id = measure.meta_data.number - 1

    new_song_new_measures.append(
        parser.API.datatypes.Measure(api_song[0].measures[m_id].meta_data,
                                     api_song[0].measures[m_id].start_time,
                                     notes_in_bars[m_id]))

new_song = parser.API.datatypes.Song(api_song[0].meta_data,
                                     new_song_new_measures)

assert new_song.measures[1].notes[-1].note.duration == Fraction(9, 8)
assert new_song.measures[1].notes[-2].note.duration == Fraction(3, 16)

parser.API.write_functions.api_to_gp5([new_song], gpfile)
guitarpro.write(gpfile, "./test_in_out.gp5")
