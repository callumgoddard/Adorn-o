from __future__ import division, print_function, absolute_import

from fractions import Fraction

import guitarpro

import cbr
from parser.API.datatypes import *
from parser.API.get_functions import *
import parser

# Read in the GP5 Test file:
gp5_file = "./gp5files/test_scores/reuse_test.gp5"
gp5song = guitarpro.parse(gp5_file)
api_test_song = parser.API.get_functions.get_song_data(gp5song)

test_song = api_test_song[0]


def get_adornment_list(adorned_notelist):
    return map(lambda an: an.adornment, adorned_notelist)


def test_select_best_adornment_for_unadorned_note(
        unadorned_note, possible_adornments, possible_dynamics,
        unadorned_measure):

    max_both = cbr.reuse_module.select_best_adornment_for_unadorned_note(
        unadorned_note,
        possible_adornments,
        possible_dynamics,
        unadorned_measure,
        complexity_weight=1,
        difficulty_weight=1,
        weight_set='RD')

    min_both = cbr.reuse_module.select_best_adornment_for_unadorned_note(
        unadorned_note,
        possible_adornments,
        possible_dynamics,
        unadorned_measure,
        complexity_weight=-1,
        difficulty_weight=-1,
        weight_set='RD')

    max_complex_min_diff = cbr.reuse_module.select_best_adornment_for_unadorned_note(
        unadorned_note,
        possible_adornments,
        possible_dynamics,
        unadorned_measure,
        complexity_weight=1,
        difficulty_weight=-1,
        weight_set='RD')

    min_complex_max_diff = cbr.reuse_module.select_best_adornment_for_unadorned_note(
        unadorned_note,
        possible_adornments,
        possible_dynamics,
        unadorned_measure,
        complexity_weight=-1,
        difficulty_weight=1,
        weight_set='RD')

    return max_both, min_both, max_complex_min_diff, min_complex_max_diff


# Testing Plucking techniques:
unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
possible_adornments = get_adornment_list(test_song.measures[1].notes +
                                         test_song.measures[2].notes)
possible_dynamics = [Dynamic('mf', None)]

max_both, min_both, max_complex_min_diff, min_complex_max_diff = (
    test_select_best_adornment_for_unadorned_note(
        unadorned_note, possible_adornments, possible_dynamics,
        unadorned_measure))

assert max_both.adornment.plucking.technique == 'double_thumb_downstroke', "max both wrong"
assert min_both.adornment.plucking.technique == 'finger', "min both wrong"
assert max_complex_min_diff.adornment.plucking.technique == 'double_thumb_downstroke', "max complex, min diff wrong"
assert min_complex_max_diff.adornment.plucking.technique == 'finger', "min complex max diff wrong"

# Testing Dynamics:
unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
possible_adornments = get_adornment_list([unadorned_note])
possible_dynamics = [
    Dynamic('fff', None),
    Dynamic('ff', None),
    Dynamic('f', None),
    Dynamic('mf', None),
    Dynamic('mp', None),
    Dynamic('p', None),
    Dynamic('pp', None),
    Dynamic('ppp', None)
]

max_both, min_both, max_complex_min_diff, min_complex_max_diff = (
    test_select_best_adornment_for_unadorned_note(
        unadorned_note, possible_adornments, possible_dynamics,
        unadorned_measure))

print(max_both.note.dynamic, min_both.note.dynamic,
      max_complex_min_diff.note.dynamic, min_complex_max_diff.note.dynamic)
assert (max_both.note.dynamic.value == 'ppp'
        and min_both.note.dynamic.value == 'mf'
        and max_complex_min_diff.note.dynamic.value == 'ppp'
        and min_complex_max_diff.note.dynamic.value == 'mf'), (
            "Dynamics are wrong")

# Testing cres/dim:
unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
possible_adornments = get_adornment_list([unadorned_note])
possible_dynamics = [
    Dynamic('fff', 'cresc'),
    Dynamic('ff', 'cresc'),
    Dynamic('f', 'cresc'),
    Dynamic('mf', 'cresc'),
    Dynamic('mp', 'cresc'),
    Dynamic('p', 'cresc'),
    Dynamic('pp', 'cresc'),
    Dynamic('ppp', 'cresc'),
    Dynamic('fff', 'dim'),
    Dynamic('ff', 'dim'),
    Dynamic('f', 'dim'),
    Dynamic('mf', 'dim'),
    Dynamic('mp', 'dim'),
    Dynamic('p', 'dim'),
    Dynamic('pp', 'dim'),
    Dynamic('ppp', 'dim'),
    Dynamic('fff', None),
    Dynamic('ff', None),
    Dynamic('f', None),
    Dynamic('mf', None),
    Dynamic('mp', None),
    Dynamic('p', None),
    Dynamic('pp', None),
    Dynamic('ppp', None)
]

max_both, min_both, max_complex_min_diff, min_complex_max_diff = (
    test_select_best_adornment_for_unadorned_note(
        unadorned_note, possible_adornments, possible_dynamics,
        unadorned_measure))

print(max_both.note.dynamic, min_both.note.dynamic,
      max_complex_min_diff.note.dynamic, min_complex_max_diff.note.dynamic)
assert (max_both.note.dynamic == Dynamic(value='ppp', cres_dim='dim')
        and min_both.note.dynamic == Dynamic(value='mf', cres_dim=None)
        and max_complex_min_diff.note.dynamic == Dynamic(
            value='ppp', cres_dim='dim')
        and min_complex_max_diff.note.dynamic == Dynamic(
            value='mf', cres_dim=None)), ("Dynamics are wrong")

# Test Fretting Techniques:
unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
possible_adornments = get_adornment_list(test_song.measures[3].notes)
possible_dynamics = [Dynamic('mf', None)]

max_both, min_both, max_complex_min_diff, min_complex_max_diff = (
    test_select_best_adornment_for_unadorned_note(
        unadorned_note, possible_adornments, possible_dynamics,
        unadorned_measure))

print(max_both.adornment.fretting.technique,
      min_both.adornment.fretting.technique,
      max_complex_min_diff.adornment.fretting.technique,
      min_complex_max_diff.adornment.fretting.technique)
assert (max_both.adornment.fretting.technique == 'pull-off'
        and min_both.adornment.fretting.technique == 'left-hand-slap'
        and max_complex_min_diff.adornment.fretting.technique == 'pull-off' and
        min_complex_max_diff.adornment.fretting.technique == 'left-hand-slap'
        ), ("Fretting Technique Selection Wrong")

unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
adorned_measure = test_song.measures[5]
adorned_notes = adorned_measure.notes

out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

print(out)
possible_dynamics = [
    Dynamic(value='fff', cres_dim=None),
    Dynamic(value='mf', cres_dim=None),
    Dynamic(value='mp', cres_dim=None),
    Dynamic(value='pp', cres_dim=None),
    Dynamic(value='ppp', cres_dim=None),
    Dynamic(value='f', cres_dim=None),
    Dynamic(value='ff', cres_dim=None),
    Dynamic(value='mf', cres_dim='cresc'),
    Dynamic(value='mf', cres_dim='dim')
]
for dynamic in possible_dynamics:
    assert dynamic in out.dynamics, "Didn't find all possible dynamics"
for p_tech in [
        'finger', 'pick_down', 'pick_up', 'slap', 'pop', 'tap',
        'double_thumb_downstroke', 'double_thumb_upstroke'
]:
    assert p_tech in out.plucking_techniques, "Didn't find all plucking techniques"
"""
for p_mod in [
        None,
        ArtificialHarmonic(
            octave=guitarpro.models.Octave(1),
            pitch=guitarpro.models.PitchClass(
                just=2, accidental=0, value=2, intonation='sharp'))
]:
    print(p_mod, out_ah.plucking_modifications_ah)
    assert p_mod in out_ah.plucking_modifications_ah, "Plucking Mod not found"
"""

for f_tech in ['fretting', 'hammer-on', 'pull-off', 'left-hand-slap']:
    assert f_tech in out.fretting_techniques, "Fretting Techinque not found"

for f_mod_type in [None, 'dead-note']:
    assert f_mod_type in out.fretting_modifications_type, "Fretting modification not found"

for t_f in [True, False]:
    assert t_f in out.plucking_modifications_palm_mute, "Palm Mute not found"
    #assert t_f in out.fretting_modifications_let_ring, "Let Ring not found"
    if t_f is True:
        assert t_f == out.fretting_modifications_let_ring

for cres_dim in [
        Dynamic(value='mf', cres_dim='cresc'),
        Dynamic(value='mf', cres_dim='dim')
]:
    assert cres_dim in out.dynamics, "cres/dim not found"

unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
adorned_measure = test_song.measures[14]
adorned_notes = parser.API.calculate_functions.calculate_tied_note_durations(
    adorned_measure)

out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

for t_f in [True, False]:
    if t_f is True:
        assert t_f == out.ghost_notes, "Ghost note not found"

for grace_note in [
        None,
        GraceNote(
            fret=4,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None)
]:
    assert grace_note in out.grace_notes, "Grace Note not found"

# Testing all the grace_note reuse stuff.
for unadorned_note, ans in zip(test_song.measures[15].notes, [[
        GraceNote(
            fret=4,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=3,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=2,
            duration=Fraction(1, 64),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=True,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
], [
        GraceNote(
            fret=5,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=4,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=3,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=True,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None)
], [
        GraceNote(
            fret=6,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=5,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=4,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=True,
            transition=None),
        GraceNote(
            fret=1,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
], [
        GraceNote(
            fret=5,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=4,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=3,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=True,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
], [
        GraceNote(
            fret=6,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=5,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=4,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=True,
            transition=None),
        GraceNote(
            fret=1,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
        GraceNote(
            fret=0,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mp', cres_dim=None),
            dead_note=False,
            on_beat=False,
            transition=None),
]]):
    unadorned_measure = test_song.measures[15]
    adorned_measure = test_song.measures[15]
    adorned_notes = adorned_measure.notes

    out = cbr.reuse_module.find_all_possible_adornements(
        unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

    print(out.grace_notes)
    for grace_note, grace_correct in zip(out.grace_notes, ans):
        if grace_note is not None:
            print(grace_correct)
            print(grace_note)
            assert grace_correct == grace_note

    out = cbr.reuse_module.find_all_possible_adornements(
        unadorned_note, [
            AdornedNote(
                note=unadorned_note.note,
                adornment=Adornment(
                    plucking=unadorned_note.adornment.plucking,
                    fretting=unadorned_note.adornment.fretting,
                    grace_note=GraceNote(
                        fret=unadorned_note.note.fret_number,
                        duration=Fraction(1, 32),
                        dynamic=Dynamic(value='mp', cres_dim=None),
                        dead_note=False,
                        on_beat=False,
                        transition='hammer'),
                    ghost_note=False))
        ], unadorned_measure, adorned_measure)
    assert out.grace_notes[0].transition == None

    out = cbr.reuse_module.find_all_possible_adornements(
        unadorned_note, [
            AdornedNote(
                note=unadorned_note.note,
                adornment=Adornment(
                    plucking=unadorned_note.adornment.plucking,
                    fretting=unadorned_note.adornment.fretting,
                    grace_note=GraceNote(
                        fret=unadorned_note.note.fret_number,
                        duration=Fraction(1, 32),
                        dynamic=Dynamic(value='mp', cres_dim=None),
                        dead_note=False,
                        on_beat=False,
                        transition='slide'),
                    ghost_note=False))
        ], unadorned_measure, adorned_measure)
    assert out.grace_notes[0].transition == None

    out = cbr.reuse_module.find_all_possible_adornements(
        unadorned_note, [
            AdornedNote(
                note=unadorned_note.note,
                adornment=Adornment(
                    plucking=unadorned_note.adornment.plucking,
                    fretting=unadorned_note.adornment.fretting,
                    grace_note=GraceNote(
                        fret=0,
                        duration=Fraction(1, 32),
                        dynamic=Dynamic(value='mp', cres_dim=None),
                        dead_note=False,
                        on_beat=False,
                        transition='bend'),
                    ghost_note=False))
        ], unadorned_measure, adorned_measure)
    assert out.grace_notes[0].transition == None

    out = cbr.reuse_module.find_all_possible_adornements(
        unadorned_note, [
            AdornedNote(
                note=unadorned_note.note,
                adornment=Adornment(
                    plucking=unadorned_note.adornment.plucking,
                    fretting=unadorned_note.adornment.fretting,
                    grace_note=GraceNote(
                        fret=unadorned_note.note.fret_number + 2,
                        duration=Fraction(1, 32),
                        dynamic=Dynamic(value='mp', cres_dim=None),
                        dead_note=True,
                        on_beat=False,
                        transition='hammer'),
                    ghost_note=False))
        ], unadorned_measure, adorned_measure)
    assert out.grace_notes[0].transition == None

unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
adorned_measure = test_song.measures[6]
adorned_notes = adorned_measure.notes

out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

print(out)

for bend in [
        Bend(
            type='bend',
            value=100,
            points=[
                BendPoint(position=0.0, value=0.0, vibrato=False),
                BendPoint(position=3.0, value=4.0, vibrato=False),
                BendPoint(position=12.0, value=4.0, vibrato=False)
            ]), None
]:
    assert bend in out.fretting_modulations_bend, "Bend not found!"
assert out.fretting_modulations_trill == [
    None
], "A trill was found when there shouldn't be one"
assert out.fretting_modulations_vib == [
    False
], "A vibrato was found when there shouldn't be one"
for slide in [None, Slide(into=None, outto='slide_legato')]:
    assert slide in out.fretting_modulations_slide, "A slide was found when there shouldn't be one"
assert True in out.plucking_accents, "Plucking Accent not found when there should have been one"
assert True in out.plucking_accents, "Plucking Accent not found when there should have been one"
assert True not in out.fretting_accents, "Fretting Accent found when it shouldn't have been"

unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
adorned_measure = test_song.measures[8]
adorned_notes = adorned_measure.notes

out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

#print(out)
assert True in out.fretting_modulations_vib, "Vib was meant to be found but wasn't"
print(out.fretting_modulations_trill)
assert Trill(
    fret=7,
    notated_duration=NotatedDuration(
        value=Fraction(1, 32),
        isDotted=False,
        isDoubleDotted=False,
        tuplet=Tuplet(
            number_of_notes=1,
            equal_to=1))) in out.fretting_modulations_trill, "Trill not found"

assert out.fretting_modulations_bend == [
    None
], "Bend found when it shouldn't have been"

unadorned_note = test_song.measures[0].notes[0]
unadorned_measure = test_song.measures[0]
adorned_measure = test_song.measures[7]
adorned_notes = adorned_measure.notes

out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)
print(out)
assert True not in out.plucking_accents, "Plucking Accent not found when there should have been one"
assert True in out.fretting_modulations_vib, "Vib wasn't found when there should have been one"
for slide in [Slide(into=None, outto='slide_shift_to'), None]:
    assert slide in out.fretting_modulations_slide, "Incorrect slide found"

assert Trill(
    fret=7,
    notated_duration=NotatedDuration(
        value=Fraction(1, 64),
        isDotted=False,
        isDoubleDotted=False,
        tuplet=Tuplet(
            number_of_notes=1,
            equal_to=1))) in out.fretting_modulations_trill, "Trill not found"

assert Trill(
    fret=9,
    notated_duration=NotatedDuration(
        value=Fraction(1, 32),
        isDotted=False,
        isDoubleDotted=False,
        tuplet=Tuplet(number_of_notes=1, equal_to=1))
) not in out.fretting_modulations_trill, "Trill found when it shouldnt have"

# Testing Hammer-on/pull-off dead-notes:
dynamics = [Dynamic('mf', None)]
plucking_accents = [False]
fretting_accents = [False]
plucking_techniques = ['finger']
plucking_modifications_ah = [None]
plucking_modifications_palm_mute = [False]
fretting_techniques = ['hammer-on', 'pull-off']
fretting_modifications_type = ['dead-note']
fretting_modifications_let_ring = [False]

fretting_modulations_bend = [None]
fretting_modulations_trill = [None]
fretting_modulations_vib = [None]
fretting_modulations_slide = [None]

grace_notes = [None]
ghost_notes = [False]

pos_adornments = cbr.reuse_module.make_all_possible_adornments(
    plucking_accents,
    fretting_accents,
    plucking_techniques,
    plucking_modifications_ah,
    plucking_modifications_palm_mute,
    fretting_techniques,
    fretting_modifications_type,
    fretting_modifications_let_ring,
    fretting_modulations_bend,
    fretting_modulations_trill,
    fretting_modulations_vib,
    fretting_modulations_slide,
    grace_notes,
    ghost_notes,
    complexity_weight=1,
    difficulty_weight=1,
    gp5_wellformedness=True)

assert 'dead-note' not in map(
    lambda x: x.fretting.modification.type,
    pos_adornments), "dead-note found when hammer-on/pull-off"

# Testing Tap:
dynamics = [Dynamic('mf', None)]
plucking_accents = [False]
fretting_accents = [False]
plucking_techniques = ['tap']
plucking_modifications_ah = [ArtificialHarmonic(3, 58)]
plucking_modifications_palm_mute = [False]
fretting_techniques = ['hammer-on', 'pull-off']
fretting_modifications_type = ['dead-note', 'natural-harmonic']
fretting_modifications_let_ring = [False]

fretting_modulations_bend = [
    Bend(
        type='bend',
        value=100,
        points=[
            BendPoint(position=0.0, value=0.0, vibrato=False),
            BendPoint(position=3.0, value=4.0, vibrato=False),
            BendPoint(position=12.0, value=4.0, vibrato=False)
        ]), None
]
fretting_modulations_trill = [
    Trill(
        fret=7,
        notated_duration=NotatedDuration(
            value=Fraction(1, 16),
            isDotted=False,
            isDoubleDotted=False,
            tuplet=Tuplet(number_of_notes=1, equal_to=1)))
]
fretting_modulations_vib = [True, False]
fretting_modulations_slide = [Slide(into=None, outto='slide_shift_to')]

grace_notes = [None]
ghost_notes = [False]

pos_adornments = cbr.reuse_module.make_all_possible_adornments(
    plucking_accents,
    fretting_accents,
    plucking_techniques,
    plucking_modifications_ah,
    plucking_modifications_palm_mute,
    fretting_techniques,
    fretting_modifications_type,
    fretting_modifications_let_ring,
    fretting_modulations_bend,
    fretting_modulations_trill,
    fretting_modulations_vib,
    fretting_modulations_slide,
    grace_notes,
    ghost_notes,
    complexity_weight=1,
    difficulty_weight=1,
    gp5_wellformedness=True)

#print(pos_adornments)

assert fretting_modulations_trill[0] not in map(
    lambda x: x.fretting.modulation.trill,
    pos_adornments), "trill found when tap"

assert 'natural-harmonic' not in map(
    lambda x: x.fretting.modification.type,
    pos_adornments), "natural-harmonic found when tap"

for ah in map(lambda x: x.plucking.modification.artificial_harmonic,
              pos_adornments):
    assert ah == None, "artificial_harmonic found when tap"

assert fretting_modulations_slide[0] in map(
    lambda x: x.fretting.modulation.slide,
    pos_adornments), "Slide not found when tap"

for bend in fretting_modulations_bend:
    assert bend in map(lambda x: x.fretting.modulation.bend,
                       pos_adornments), "Bend not found when tap"

for vib in fretting_modulations_vib:
    assert vib in map(lambda x: x.fretting.modulation.vibrato,
                      pos_adornments), "Vibrato not found when tap"

# Testing Trill:
dynamics = [Dynamic('mf', None)]
plucking_accents = [False]
fretting_accents = [False]
plucking_techniques = [
    'finger', 'pick_down', 'pick_up', 'slap', 'pop', 'double_thumb_downstroke',
    'double_thumb_upstroke'
]
plucking_modifications_ah = [ArtificialHarmonic(3, 58)]
plucking_modifications_palm_mute = [False]
fretting_techniques = ['hammer-on', 'pull-off']
fretting_modifications_type = ['dead-note', 'natural-harmonic']
fretting_modifications_let_ring = [False]

fretting_modulations_bend = [
    Bend(
        type='bend',
        value=100,
        points=[
            BendPoint(position=0.0, value=0.0, vibrato=False),
            BendPoint(position=3.0, value=4.0, vibrato=False),
            BendPoint(position=12.0, value=4.0, vibrato=False)
        ]), None
]
fretting_modulations_trill = [
    Trill(
        fret=7,
        notated_duration=NotatedDuration(
            value=Fraction(1, 16),
            isDotted=False,
            isDoubleDotted=False,
            tuplet=Tuplet(number_of_notes=1, equal_to=1)))
]
fretting_modulations_vib = [True, False]
fretting_modulations_slide = [Slide(into=None, outto='slide_shift_to')]

grace_notes = [None]
ghost_notes = [False]

pos_adornments = cbr.reuse_module.make_all_possible_adornments(
    plucking_accents,
    fretting_accents,
    plucking_techniques,
    plucking_modifications_ah,
    plucking_modifications_palm_mute,
    fretting_techniques,
    fretting_modifications_type,
    fretting_modifications_let_ring,
    fretting_modulations_bend,
    fretting_modulations_trill,
    fretting_modulations_vib,
    fretting_modulations_slide,
    grace_notes,
    ghost_notes,
    complexity_weight=1,
    difficulty_weight=1,
    gp5_wellformedness=True)

for pa in pos_adornments:
    assert pa.plucking.technique in plucking_techniques, "Plucking technique missing"
    assert pa.fretting.technique in fretting_techniques, "Fretting technique missing"

    if isinstance(pa.fretting.modulation.trill, Trill):
        assert pa.fretting.modification.type == None, "fretting mod is incompatible with trill"
        assert pa.plucking.modification.artificial_harmonic is None, "ArtificialHarmonic can't be played with trill"
        assert pa.fretting.modulation.slide is None, "Slide can't be played with trill"
    if pa.fretting.modification.type == 'natural-harmonic':
        assert pa.plucking.modification.artificial_harmonic is None, "ArtificialHarmonic can't be played with natural-harmonic"
    if pa.fretting.modification.type == 'dead-note':
        assert pa.plucking.modification.artificial_harmonic is None, "ArtificialHarmonic can't be played with dead-note"
    if pa.plucking.modification.artificial_harmonic is not None:
        assert pa.fretting.modification.type == None, "fretting mod is incompatible with artificial_harmonic"

# Testing Grace note stuff:

# Testing Hammer-on/pull-off dead-notes:
dynamics = [Dynamic('mf', None)]
plucking_accents = [False]
fretting_accents = [False]
plucking_techniques = ['finger']
plucking_modifications_ah = [
    None, None,
    ArtificialHarmonic(3, 58), None, None,
    ArtificialHarmonic(3, 58), None
]
plucking_modifications_palm_mute = [False]
fretting_techniques = ['fretting']
fretting_modifications_type = [
    'dead-note', 'harmonic', None, 'dead-note', 'harmonic', None, 'dead-note'
]
fretting_modifications_let_ring = [False]

fretting_modulations_bend = [None]
fretting_modulations_trill = [None]
fretting_modulations_vib = [None]
fretting_modulations_slide = [None]

ghost_notes = [None]

grace_notes = [
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=True,
        on_beat=False,
        transition='hammer'),
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=True,
        on_beat=False,
        transition='hammer'),
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=True,
        on_beat=False,
        transition='hammer'),
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=True,
        on_beat=False,
        transition='slide'),
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=True,
        on_beat=False,
        transition='slide'),
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=True,
        on_beat=False,
        transition='slide'),
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=True,
        on_beat=False,
        transition='bend'),
    GraceNote(
        fret=4,
        duration=Fraction(1, 32),
        dynamic=Dynamic(value='mf', cres_dim=None),
        dead_note=False,
        on_beat=False,
        transition='bend')
]

pos_adornments = cbr.reuse_module.make_all_possible_adornments(
    plucking_accents,
    fretting_accents,
    plucking_techniques,
    plucking_modifications_ah,
    plucking_modifications_palm_mute,
    fretting_techniques,
    fretting_modifications_type,
    fretting_modifications_let_ring,
    fretting_modulations_bend,
    fretting_modulations_trill,
    fretting_modulations_vib,
    fretting_modulations_slide,
    grace_notes,
    ghost_notes,
    complexity_weight=1,
    difficulty_weight=1,
    gp5_wellformedness=True)

for pa in pos_adornments:

    if pa.fretting.modification.type == 'dead-note':
        assert pa.grace_note.transition not in ['bend']
        if pa.grace_note.dead_note:
            assert pa.grace_note.transition not in ['slide']

    if pa.fretting.modification.type == 'harmonic':
        assert pa.grace_note.transition not in ['hammer', 'slide']

    if isinstance(pa.plucking.modification.artificial_harmonic,
                  ArtificialHarmonic):
        assert pa.grace_note.transition not in ['hammer', 'slide']

# Testing chunking and match_up_unadorned_notes_with_adorned_notes()
# stuff - it uses fantastic:

unadorned_measure = test_song.measures[9]
adorned_measure = test_song.measures[10]
out = cbr.reuse_module.chunk_up_a_measure(unadorned_measure)

for chunk, ans in zip(out, [[1, 2, 3], [2, 3, 5], [3, 5, 6]]):
    assert map(lambda us: us.note.note_number,
               chunk) == ans, "Chunk done wrong"

unadorned_measure = test_song.measures[0]
out = cbr.reuse_module.chunk_up_a_measure(unadorned_measure, chunk_size=3)

for chunk, ans in zip(out, [[1]]):
    print(map(lambda us: us.note.note_number, chunk))
    assert map(lambda us: us.note.note_number,
               chunk) == ans, "Chunk done wrong"

unadorned_measure = test_song.measures[9]
unadorned_measure_notes = parser.API.calculate_functions.calculate_tied_note_durations(
    unadorned_measure)
adorned_measure = test_song.measures[10]
# Check a measure will match the chunks to itself:
unadorned_chunks, matched = cbr.reuse_module.match_up_unadorned_measure_chunks_with_adorned_measure_chunks(
    unadorned_measure,
    unadorned_measure_notes,
    unadorned_measure,
    chunk_size=3)

for ua_chunk, matched_chunks in zip(unadorned_chunks, matched):

    ua_chunk_notes = map(lambda us: us.note.note_number, ua_chunk)
    for matched_chunk in matched_chunks:
        matched_chunk_notes = map(lambda us: us.note.note_number,
                                  matched_chunk)
        print(ua_chunk_notes, matched_chunk_notes)
        assert ua_chunk_notes == matched_chunk_notes, "Matched sequences are incorrect"

# Check a measure will match the chunks to itself:
unadorned_chunks, matched = cbr.reuse_module.match_up_unadorned_measure_chunks_with_adorned_measure_chunks(
    unadorned_measure,
    unadorned_measure_notes,
    unadorned_measure,
    chunk_size=2)

for ua_chunk, matched_chunks in zip(unadorned_chunks, matched):

    ua_chunk_notes = map(lambda us: us.note.note_number, ua_chunk)
    for matched_chunk in matched_chunks:
        matched_chunk_notes = map(lambda us: us.note.note_number,
                                  matched_chunk)
        print(ua_chunk_notes, matched_chunk_notes)
        assert ua_chunk_notes == matched_chunk_notes, "Matched sequences are incorrect"

# Check a measure will match the chunks to itself:
unadorned_chunks, matched = cbr.reuse_module.match_up_unadorned_measure_chunks_with_adorned_measure_chunks(
    unadorned_measure,
    unadorned_measure_notes,
    unadorned_measure,
    chunk_size=1)

for ua_chunk, matched_chunks in zip(unadorned_chunks, matched):

    ua_chunk_pitches = map(lambda us: us.note.pitch, ua_chunk)
    ua_chunk_fret = map(lambda us: us.note.fret_number, ua_chunk)
    ua_chunk_string = map(lambda us: us.note.string_number, ua_chunk)
    for matched_chunk in matched_chunks:
        print(ua_chunk_notes)
        print(matched_chunk)

        matched_chunk_pitches = map(lambda us: us.note.pitch, matched_chunk)
        matched_chunk_fret = map(lambda us: us.note.fret_number, matched_chunk)
        matched_chunk_string = map(lambda us: us.note.string_number,
                                   matched_chunk)
        print(ua_chunk_notes, matched_chunk_notes)
        assert ua_chunk_pitches == matched_chunk_pitches, "Matched sequences are incorrect"
        assert ua_chunk_fret == matched_chunk_fret, "Matched sequences are incorrect"
        assert ua_chunk_string == matched_chunk_string, "Matched sequences are incorrect"

unadorned_chunks, matched = cbr.reuse_module.match_up_unadorned_measure_chunks_with_adorned_measure_chunks(
    unadorned_measure, unadorned_measure_notes, adorned_measure, chunk_size=3)

for ua_chunk, matched_chunks, ans in zip(unadorned_chunks, matched,
                                         [[4, 5, 6], [1, 2, 4], [1, 2, 4]]):

    ua_chunk_notes = map(lambda us: us.note.note_number, ua_chunk)
    for matched_chunk in matched_chunks:
        matched_chunk_notes = map(lambda us: us.note.note_number,
                                  matched_chunk)
        print(ua_chunk_notes, matched_chunk_notes)
        assert matched_chunk_notes == ans, "Matched sequences are incorrect"

# note: this is all wrong:
matched_notes = cbr.reuse_module.consolidate_note_sequnces_matches_to_note_matches(
    unadorned_chunks, matched)

for note, ans in zip(
        matched_notes,
    [[1, [4]], [2, [5, 1]], [3, [6, 2, 1]], [5, [4, 2]], [6, [4]]]):

    #[[1, [4]], [2, [5, 1, 2]], [3, [6, 2, 4, 1]], [5, [4, 5, 2]], [6, [4]]]):
    assert note.unadorned_note.note.note_number == ans[
        0], "unadorned_note consolidated wrong"
    #print(map(
    #    lambda us: us.note.note_number,
    #    note.adorned_notes))
    #print(ans[1])
    assert map(
        lambda us: us.note.note_number,
        note.adorned_notes) == ans[1], "adorned notes consolidated wrong"

# Testing the full reuse function:
test_full_functions = False
# test_full_functions = True
if test_full_functions:
    print("testing adorn_unadorned_note will all possible adornments:")
    # All the functions together:
    unadorned_note = test_song.measures[0].notes[0]
    unadorned_measure = test_song.measures[0]
    adorned_measure = test_song.measures[5]
    adorned_notes = adorned_measure.notes
    complexity_weight = 1
    difficulty_weight = 1

    best_note = cbr.reuse_module.adorn_unadorned_note(
        unadorned_note, adorned_notes, unadorned_measure, adorned_measure,
        complexity_weight, difficulty_weight)

    print("best note: ", best_note)

# testing chunk sizes of 1
unadorned_measure = test_song.measures[1]
out = cbr.reuse_module.chunk_up_a_measure(unadorned_measure, chunk_size=1)

for chunk, ans in zip(out, [[1], [2], [3], [4]]):
    print(map(lambda us: us.note.note_number, chunk))
    assert map(lambda us: us.note.note_number,
               chunk) == ans, "Chunk done wrong"

# testing chunk sizes of 2
unadorned_measure = test_song.measures[1]
out = cbr.reuse_module.chunk_up_a_measure(unadorned_measure, chunk_size=2)

for chunk, ans in zip(out, [[1, 2], [2, 3], [3, 4]]):
    print(map(lambda us: us.note.note_number, chunk))
    assert map(lambda us: us.note.note_number,
               chunk) == ans, "Chunk done wrong"

most_similar = cbr.reuse_module.find_most_similar_notes(
    [test_song.measures[0].notes[0]], test_song.measures[1])

for notes in most_similar:
    print(map(lambda us: us.note.note_number, notes))

con_test = cbr.reuse_module.consolidate_note_sequnces_matches_to_note_matches(
    [[test_song.measures[0].notes[0]]], [most_similar])

assert len(con_test) == 1
assert con_test[0].unadorned_note == test_song.measures[0].notes[0]
assert map(lambda us: us.note.note_number,
           con_test[0].adorned_notes) == [1, 2, 3, 4]

# Test harmonics:
unadorned_measure = test_song.measures[11]
adorned_measure = test_song.measures[12]
unadorned_note = test_song.measures[11].notes[0]
adorned_notes = [test_song.measures[12].notes[0]]
out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

assert out.fretting_modifications_type == ['natural-harmonic']

unadorned_measure = test_song.measures[0]
unadorned_note = test_song.measures[0].notes[0]
out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

assert out.fretting_modifications_type == [None]

unadorned_measure = test_song.measures[11]
adorned_measure = test_song.measures[12]
unadorned_note = test_song.measures[11].notes[1]
adorned_notes = [test_song.measures[12].notes[1]]
out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

assert out.plucking_modifications_ah == [
    ArtificialHarmonic(
        octave=guitarpro.models.Octave(1),
        pitch=guitarpro.models.PitchClass(
            just=7, accidental=0, value=7, intonation='sharp'))
]

unadorned_measure = test_song.measures[0]
unadorned_note = test_song.measures[0].notes[0]
out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

assert out.plucking_modifications_ah == [None]

# Testing harmonic and palm_muting:
unadorned_measure = test_song.measures[11]
adorned_measure = test_song.measures[12]
unadorned_note = test_song.measures[11].notes[0]
adorned_notes = [
    test_song.measures[12].notes[0], test_song.measures[12].notes[2]
]
out = cbr.reuse_module.find_all_possible_adornements(
    unadorned_note, adorned_notes, unadorned_measure, adorned_measure)

print(out.fretting_modifications_type, out.plucking_modifications_palm_mute)

harm_mute = cbr.reuse_module.make_all_possible_adornments(
    out.plucking_accents,
    out.fretting_accents,
    out.plucking_techniques,
    out.plucking_modifications_ah,
    out.plucking_modifications_palm_mute,
    out.fretting_techniques,
    out.fretting_modifications_type,
    out.fretting_modifications_let_ring,
    out.fretting_modulations_bend,
    out.fretting_modulations_trill,
    out.fretting_modulations_vib,
    out.fretting_modulations_slide,
    out.grace_notes,
    out.ghost_notes,
    complexity_weight=1,
    difficulty_weight=1,
    gp5_wellformedness=True)

print(len(harm_mute))
print(harm_mute)

best_note = cbr.reuse_module.select_best_adornment_for_unadorned_note(
    unadorned_note,
    harm_mute, [Dynamic('mf', None)],
    unadorned_measure,
    1,
    1,
    weight_set='RD')
print(harm_mute)
print(best_note)
assert best_note.adornment.plucking.modification.palm_mute
assert best_note.adornment.fretting.modification.type == 'natural-harmonic'

tol_gp5_file = "./gp5files/Listening-test-mono/tol.gp5"
tol_gp5song = guitarpro.parse(tol_gp5_file)
api_song = parser.API.get_functions.get_song_data(tol_gp5song)
tol = api_song[0]

h_gp5_file = "./gp5files/Listening-test-mono/h-official.gp5"
h_gp5song = guitarpro.parse(h_gp5_file)
api_song = parser.API.get_functions.get_song_data(h_gp5song)
h = api_song[0]

r_gp5_file = "./gp5files/Listening-test-mono/r.gp5"
r_gp5song = guitarpro.parse(r_gp5_file)
api_song = parser.API.get_functions.get_song_data(r_gp5song)
r = api_song[0]

c_gp5_file = "./gp5files/Listening-test-mono/c.gp5"
c_gp5song = guitarpro.parse(c_gp5_file)
api_song = parser.API.get_functions.get_song_data(c_gp5song)
c = api_song[0]

s_gp5_file = "./gp5files/Listening-test-mono/s.gp5"
s_gp5song = guitarpro.parse(s_gp5_file)
api_song = parser.API.get_functions.get_song_data(s_gp5song)
s = api_song[0]

sd_gp5_file = "./gp5files/Listening-test-mono/sd.gp5"
sd_gp5song = guitarpro.parse(s_gp5_file)
api_song = parser.API.get_functions.get_song_data(sd_gp5song)
sd = api_song[0]

wdytiw_gp5_file = "./gp5files/Listening-test-mono/wdytiw.gp5"
wdytiw_gp5song = guitarpro.parse(wdytiw_gp5_file)
api_song = parser.API.get_functions.get_song_data(wdytiw_gp5song)
wdytiw = api_song[0]

#adorned_measures = [tol.measures[0], h.measures[1], r.measures[0]]

unadorned_measure = tol.measures[0]
#new_measures, combined_measure = cbr.reuse_measures(unadorned_measure,
#                                                    adorned_measures)
adorned_measures = tol.measures + h.measures + r.measures + c.measures + s.measures + sd.measures + wdytiw.measures

new_measures = cbr.reuse_module.reuse_measures(
    unadorned_measure=unadorned_measure,
    unadorned_measure_notes=parser.API.calculate_functions.
    calculate_tied_note_durations(unadorned_measure),
    adorned_measures=adorned_measures,
    complexity_weight=1,
    difficulty_weight=1,
    weight_set='RD',
)

assert len(new_measures) == 15

for measure in new_measures:
    print("\nnew_measure:")
    for note, note_number in zip(measure.notes, [1, 2, 3, 4]):
        assert note.note.note_number == note_number
        print('\n', note)
"""
new_measure = cbr.reuse(
    unadorned_measure,
    adorned_measures,
    complexity_weight=1,
    difficulty_weight=1,
    gp5_wellformedness=True)

"""
