

from fractions import Fraction

import guitarpro

import cbr.revision
from parser.API.datatypes import *
from parser.API.get_functions import get_song_data
from parser.API.update_functions import (update_adorned_note,
                                         update_fretting_in_adornment)
from parser.API.calculate_functions import calculate_tied_note_durations, calculate_bars_from_note_list

# Read in the GP5 Test file:
gp5_file = "./gp5files/test_scores/revise_test.gp5"
gp5song = guitarpro.parse(gp5_file)
api_test_song = get_song_data(gp5song)

test_song = api_test_song[0]

####### Testing Hammer-on/pull-off revision:

# test technique replacement in hammer-on-pull-offs:
ans = []
for n1, n2 in zip(test_song.measures[6].notes[::],
                  test_song.measures[6].notes[1::]):
    out = cbr.revision.revise_fretting_technique(n2, n1)
    n2, n1 = cbr.revision.revise_note_pair(n2, n1, test_song.measures[6])
    if out[0] in ['hammer-on', 'pull-off']:
        assert out[1] == 'finger'
        assert n2.adornment.plucking.technique == 'finger'

# make all notes hammer-on
technique = 'hammer-on'
for note in test_song.measures[0].notes:

    index = test_song.measures[0].notes.index(note)
    new_adornment = update_fretting_in_adornment(
        note.adornment.fretting, note.adornment, technique=technique)

    updated_note = update_adorned_note(note, adornment=new_adornment)
    test_song.measures[0].notes[index] = updated_note

    #print(test_song.measures[0].notes[test_song.measures[0].notes.index(updated_note)].adornment.fretting)
    assert test_song.measures[0].notes[test_song.measures[0].notes.index(
        updated_note
    )].adornment.fretting.technique == technique, "Technique didn't update correctly"

# testing
for prev_note, current_note, ans in zip(test_song.measures[0].notes[::],
                                        test_song.measures[0].notes[1::],
                                        ['hammer-on', 'pull-off', None]):
    print(prev_note, current_note, ans)
    new_fretting, new_pluck = cbr.revision.revise_fretting_technique(
        current_note, prev_note)
    assert new_fretting == ans, "hammer-on didn't revise correctly"
    if new_fretting in ['hammer-on', 'pull-off']:
        assert new_pluck == 'finger'
    else:
        assert new_pluck == current_note.adornment.plucking.technique

# make all notes pull-off
technique = 'pull-off'
for note in test_song.measures[0].notes:

    index = test_song.measures[0].notes.index(note)
    new_adornment = update_fretting_in_adornment(
        note.adornment.fretting, note.adornment, technique=technique)

    updated_note = update_adorned_note(note, adornment=new_adornment)
    test_song.measures[0].notes[index] = updated_note

    # print(test_song.measures[0].notes[test_song.measures[0].notes.index(updated_note)].adornment.fretting)
    assert test_song.measures[0].notes[test_song.measures[0].notes.index(
        updated_note
    )].adornment.fretting.technique == technique, "Technique didn't update correctly"

# testing
for prev_note, current_note, ans in zip(test_song.measures[0].notes[::],
                                        test_song.measures[0].notes[1::],
                                        ['hammer-on', 'pull-off', None]):
    new_fretting, new_pluck = cbr.revision.revise_fretting_technique(
        current_note, prev_note)
    assert new_fretting == ans, "hammer-on didn't revise correctly"
    if new_fretting in ['hammer-on', 'pull-off']:
        assert new_pluck == 'finger'
    else:
        assert new_pluck == current_note.adornment.plucking.technique

note = test_song.measures[0].notes[1]
new_adornment = update_fretting_in_adornment(
    note.adornment.fretting,
    note.adornment,
    modification=FrettingModification('natural-harmonic', False))
updated_note = update_adorned_note(note, adornment=new_adornment)
new_fretting, new_plucking = cbr.revision.revise_fretting_technique(
    test_song.measures[0].notes[2], updated_note)
assert new_fretting is None
assert new_pluck == current_note.adornment.plucking.technique

# Testing String crossing code:
assert cbr.revision.string_crossing_check(
    test_song.measures[1].notes[2],
    test_song.measures[1].notes[1]), "String crossing check is wrong"
assert cbr.revision.string_crossing_check(
    test_song.measures[1].notes[2],
    test_song.measures[1].notes[1]) == -1, "String crossing check is wrong"
assert not cbr.revision.string_crossing_check(
    test_song.measures[1].notes[0],
    test_song.measures[1].notes[1]), "String crossing check is wrong"

# testing revise_slap_pop_pattern()
for current_note, prev_note, ans in zip(
        test_song.measures[1].notes[::], test_song.measures[1].notes[1::],
    [['slap', 'slap'], ['slap', 'pop'], ['slap', 'pop']]):

    slap_pop_order = cbr.revision.revise_slap_pop_pattern(
        current_note, prev_note)
    assert slap_pop_order.current_note == ans[0]
    assert slap_pop_order.previous_note == ans[1]

# Testing: revise_for_gp5_output
note = test_song.measures[0].notes[1]
new_adornment = update_fretting_in_adornment(
    note.adornment.fretting,
    note.adornment,
    modulation=Modulation(None, None, Trill(5, 'test'), None))
updated_note = update_adorned_note(note, adornment=new_adornment)
assert cbr.revision.revise_for_gp5_output(test_song.measures[0].notes[2],
                                          updated_note) is None

note = test_song.measures[0].notes[1]
new_adornment = update_fretting_in_adornment(
    note.adornment.fretting,
    note.adornment,
    modulation=Modulation(None, None, None, Slide('in', 'out')))
updated_note = update_adorned_note(note, adornment=new_adornment)
assert cbr.revision.revise_for_gp5_output(test_song.measures[0].notes[2],
                                          updated_note) is None

measure = test_song.measures[2]
answers = [['pick_down', 'pick_up'], ['pick_down',
                                      'pick_down'], ['pick_down', 'pick_down'],
           ['pick_down', 'double_thumb_downstroke'], [
               'double_thumb_downstroke', 'double_thumb_upstroke'
           ], ['double_thumb_upstroke', 'double_thumb_upstroke'],
           ['double_thumb_upstroke', 'double_thumb_upstroke']]
for previous_note, current_note, ans in zip(measure.notes[::],
                                            measure.notes[1::], answers):

    pick_order = cbr.revision.revise_stroke_directions(current_note,
                                                       previous_note, measure)

    assert pick_order.current_note == ans[1]
    assert pick_order.previous_note == ans[0]

measure = test_song.measures[3]
notes = calculate_tied_note_durations(measure)
answers = [['pick_down', 'pick_up'], ['pick_up', 'pick_down'],
           ['pick_down', 'pick_up'], ['pick_up',
                                      'pick_up'], ['pick_up', 'pick_up'], []]
for previous_note, current_note, ans in zip(notes[::], notes[1::], answers):
    pick_order = cbr.revision.revise_stroke_directions(current_note,
                                                       previous_note, measure)
    print(pick_order)
    print(ans)
    assert pick_order.current_note == ans[1]
    assert pick_order.previous_note == ans[0]

measure = test_song.measures[4]
notes = calculate_tied_note_durations(measure)
answer = [['pick_down', 'pick_up'], ['pick_up', 'pick_down'],
          ['pick_down', 'pick_up'], ['pick_up',
                                     'pick_down'], ['pick_down', 'pick_up']]
for previous_note, current_note, ans in zip(notes[::], notes[1::], answers):
    pick_order = cbr.revision.revise_stroke_directions(current_note,
                                                       previous_note, measure)
    #print(pick_order)
    assert pick_order.current_note == ans[1]
    assert pick_order.previous_note == ans[0]

measure = test_song.measures[5]
notes = calculate_tied_note_durations(measure)
answer = [['pick_down', 'pick_up'], ['pick_up', 'pick_down'],
          ['pick_down', 'pick_up'], ['pick_up',
                                     'pick_down'], ['pick_down', 'pick_up']]
for previous_note, current_note, ans in zip(notes[::], notes[1::], answers):
    pick_order = cbr.revision.revise_stroke_directions(current_note,
                                                       previous_note, measure)
    print(pick_order)
    assert pick_order.current_note == ans[1]
    assert pick_order.previous_note == ans[0]

previous_note = AdornedNote(
    Note('note_number', 'pitch', 'fret_number', 'string_number',
         'string_tuning', 'start_time', 'duration', 'notated_duration',
         'dynamic'),
    Adornment(
        PluckingAdornment('plucking_technique', 'modification', 'accent'),
        FrettingAdornment(
            'technique', 'modification', 'accent',
            Modulation('bend', 'vibrato', 'trill', Slide(None, None))), None,
        False))

slides = [
    Slide('slide_from_below', 'slide_out_below'),
    Slide(None, None),
    Slide(None, None),
    Slide(None, None),
    Slide(None, None)
]
plucking_techs = ['tap', 'tap', 'finger', 'finger']
string_numbers = [1, 2, 3, 4]
ans = [[Slide(None, 'slide_out_below'), 'plucking_technique'],
       [None, 'plucking_technique'], [None, 'finger'], [None, 'finger']]
prev_notes = [previous_note, previous_note, previous_note, None]

for slide, plucking_tech, string_number, an, previous_note in zip(
        slides, plucking_techs, string_numbers, ans, prev_notes):
    current_note = AdornedNote(
        Note(
            note_number=1,
            pitch=50,
            fret_number=0,
            string_number=string_number,
            string_tuning={
                1: 56,
                2: 46,
                3: 36,
                4: 28
            },
            start_time=0,
            duration=0,
            notated_duration=0,
            dynamic='mf'),
        Adornment(
            PluckingAdornment(plucking_tech, 'modification', 'accent'),
            FrettingAdornment('technique', 'modification', 'accent',
                              Modulation('bend', 'vibrato', 'trill', slide)),
            None, False))

    current_note_changes, prevous_note_changes = cbr.revision.revise_open_string_restrictions(
        current_note, previous_note)
    print(current_note_changes, an)
    print(prevous_note_changes)
    assert current_note_changes.slide == an[0]
    assert current_note_changes.technique == an[1]

slides = [
    Slide('slide_from_below', 'slide_out_below'),
    Slide(None, 'slide_out_above'),
    Slide(None, 'slide_shift_to'),
    Slide(None, 'slide_legato'),
    Slide(None, None)
]
plucking_techs = ['tap', 'tap', 'finger', 'tap']
string_numbers = [1, 2, 3, 4]
ans = [[None, 'finger'], [None, 'finger'], [None, 'finger'], [None, 'slap']]

ms = [None, None, None, test_song.measures[1]]

for slide, plucking_tech, string_number, an, m in zip(slides, plucking_techs,
                                                      string_numbers, ans, ms):
    current_note = AdornedNote(
        Note(
            note_number=1,
            pitch=50,
            fret_number=0,
            string_number=string_number,
            string_tuning={
                1: 56,
                2: 46,
                3: 36,
                4: 28
            },
            start_time=0,
            duration=0,
            notated_duration=0,
            dynamic='mf'),
        Adornment(
            PluckingAdornment(plucking_tech, 'modification', 'accent'),
            FrettingAdornment('technique', 'modification', 'accent',
                              Modulation('bend', 'vibrato', 'trill', slide)),
            None, False))

    current_note_changes, prevous_note_changes = cbr.revision.revise_open_string_restrictions(
        current_note, current_note, m)
    print(prevous_note_changes, an)
    assert prevous_note_changes.slide == an[0]
    assert prevous_note_changes.technique == an[1]

# Read in the GP5 Test file:
gp5_file = "./gp5files/test_scores/test_slide_shift.gp5"
gp5song = guitarpro.parse(gp5_file)
api_test_song = get_song_data(gp5song)

note_list = calculate_tied_note_durations(api_test_song[0])
note_list_for_each_measure = calculate_bars_from_note_list(
    note_list, api_test_song[0])

ans = [
    [None, Slide(into=None, outto='slide_shift_to')],
    [None, Slide(into=None, outto='slide_legato')],
    [None, Slide(into='slide_from_below', outto=None)],
    [
        Slide(into='slide_from_below', outto=None),
        Slide(into=None, outto='slide_legato')
    ],
    [None, Slide(into='slide_from_below', outto='slide_legato')],
    [
        Slide(into='slide_from_below', outto='slide_out_above'),
        Slide(into=None, outto='slide_legato')
    ],
    [None, Slide(into='slide_from_above', outto=None)],
    [
        Slide(into='slide_from_above', outto=None),
        Slide(into=None, outto='slide_shift_to')
    ],
    [
        Slide(into=None, outto='slide_out_below'),
        Slide(into=None, outto='slide_legato')
    ],
    [
        Slide(into=None, outto='slide_out_below'),
        Slide(into=None, outto='slide_legato')
    ],
    [Slide(into=None, outto='slide_out_above'), None],
    [None, Slide(into=None, outto='slide_legato')],
    [None, None],
    [None, Slide(into=None, outto='slide_legato')],
    [None, None],
    [None, Slide(into=None, outto='slide_legato')],
    [
        Slide(into=None, outto='slide_out_above'),
        Slide(into=None, outto='slide_legato')
    ],
    [Slide(into=None, outto='slide_out_below'), None],
]

previous_note = None
answer = 0
for measure in api_test_song[0].measures:
    measure_id = measure.meta_data.number - 1

    for current_note in note_list_for_each_measure[measure_id]:
        if previous_note == None:
            previous_note = current_note
            continue

        current_note, previous_note = cbr.revision.revise_note_pair(
            current_note, previous_note, measure)
        assert previous_note.adornment.fretting.modulation.slide == ans[
            answer][0]
        assert current_note.adornment.fretting.modulation.slide == ans[answer][
            1]
        previous_note = current_note
        answer += 1


###

# Need to test:
#cbr.revision.revise_measure(test_song.measures[0])
#revise_measure_transitions()

#revise_note_pair()
#cbr.revision.revise_song(api_test_song[0], True)

#revise()
