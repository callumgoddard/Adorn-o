

from fractions import Fraction

from parser.API.update_functions import *
from parser.API.datatypes import *

updated_rest = update_rest(
    rest=Rest(1, Fraction(0, 1), Fraction(1, 4),
              NotatedDuration(Fraction(1, 4), False, False, Tuplet(1, 1))),
    note_number=2,
    start_time=Fraction(1, 4),
    duration=Fraction(1, 8),
    notated_duration=NotatedDuration(
        Fraction(1, 8), False, False, Tuplet(1, 1)))

assert updated_rest.note_number == 2
assert updated_rest.start_time == Fraction(1, 4)
assert updated_rest.duration == Fraction(1, 8)
assert updated_rest.notated_duration == NotatedDuration(
    Fraction(1, 8), False, False, Tuplet(1, 1))

updated_note = update_note(
    Note(
        note_number=1,
        pitch=48,
        fret_number=5,
        string_number=4,
        string_tuning="string_tuning",
        start_time=Fraction(0, 1),
        duration=Fraction(1, 4),
        notated_duration=NotatedDuration(
            Fraction(1, 4), False, False, Tuplet(1, 1)),
        dynamic=Dynamic('f', None)),
    note_number=2,
    pitch=30,
    fret_number=4,
    string_number=2,
    string_tuning="string_tuning",
    start_time=Fraction(1, 4),
    duration=Fraction(1, 8),
    notated_duration=NotatedDuration(
        Fraction(1, 8), False, False, Tuplet(1, 1)),
    dynamic=Dynamic('mf', None))

assert updated_note == Note(
    note_number=2,
    pitch=30,
    fret_number=4,
    string_number=2,
    string_tuning="string_tuning",
    start_time=Fraction(1, 4),
    duration=Fraction(1, 8),
    notated_duration=NotatedDuration(
        Fraction(1, 8), False, False, Tuplet(1, 1)),
    dynamic=Dynamic('mf', None))

update_adornment()

update_plucking_adornment()

update_fretting_adornment()

update_modulation()

update_modulation_in_fretting_adornment()

update_plucking_in_adorment()

update_fretting_in_adornment()

update_adornment_in_adorned_note()

update_note_in_adorned_note()

update_adorned_note()

update_note_in_measure()

update_measure_in_song()

update_measure_meta_data()

add_measure_to_song()
