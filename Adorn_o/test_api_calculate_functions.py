

from fractions import Fraction

import guitarpro

from parser.API.get_functions import *
from parser.API.calculate_functions import *
from parser.API.datatypes import *
from evaluation import musiplectics

dummy_meta_data = MeasureMetaData(
    title='dummy',
    number=1,
    key_signature='CMajor',
    time_signature='4/4',
    tempo=120,
    triplet_feel=None,
    monophonic=True,
    only_tied_notes=False,
    only_rests=False)

dummy_measure = Measure(meta_data=dummy_meta_data, start_time=0, notes=[])

dummy_note = Note(
    note_number=1,
    pitch=48,
    fret_number=5,
    string_number=1,
    string_tuning={
        1: 43,
        2: 38,
        3: 33,
        4: 28
    },
    start_time=Fraction(0, 4),
    duration=Fraction(1, 4),
    notated_duration=NotatedDuration('value', 'isDotted', 'isDoubleDotted',
                                     'tuplet'),
    dynamic=Dynamic("ff", "cresc"))

plucking = PluckingAdornment('technique', PluckingModification(False, None),
                             'accent')
modulation = Modulation(None, None, None, None)
fretting = FrettingAdornment(
    'technique',
    FrettingModification(None, False),
    'accent',
    modulation=modulation)
grace_note = None
ghost_note = False
dummy_adornment = Adornment(
    plucking=plucking,
    fretting=fretting,
    grace_note=grace_note,
    ghost_note=ghost_note)

dummy_adorned_note = AdornedNote(dummy_note, dummy_adornment)

#### Testing general functions
assert calculate_measure_duration(
    dummy_measure) == 1, "Calculate Measure is wrong"
"""
calculate_measure_endtime()
calculate_song_duration()
calculate_note_endtime()
calculate_note_duration()
calculate_duration_for_notes_in_measure()
calculate_duration_for_notes_in_song()
calculate_measure_polyphony()
calculate_polyphony_for_measures_in_a_song()
calculate_only_tied_notes_measure()
calculate_only_rests_measure()
calcaulate_endtime()
calculate_time_sig_denominator()
calculate_time_sig_numerator()
calculate_pitch_interval()
calculate_note_pitch()
calculate_note_pitch_fretted()
calculate_note_pitch_harmonic()
calculate_note_pitch_artificial_harmonic()
calculate_artificial_harmonic_interval()
calculate_artificial_harmonic_octave()

calculate_bars_from_note_list()
calculate_midi_file_for_measure_note_list()
calculate_midi_files()
calculate_rhy_file_for_measure()
calculate_rhy_file_for_song()
"""

#### Testing Musiplectic Functions:
assert calculate_realtime_duration(Fraction(
    1, 4), 120) == 500, "Real time duration calculation is wrong"

assert calculate_closest_value(
    [1, 5, 6, 10], 3, return_type='smallest'
) == 1, "Calculate_closest_value return_type smallest is wrong"
assert calculate_closest_value(
    [1, 5, 6, 10], 3, return_type='largest'
) == 5, "Calculate_closest_value return_type largest is wrong"
assert calculate_closest_value(
    [1, 5, 6, 10], 3, return_type='closest'
) == 5, "Calculate_closest_value return_type closest is wrong"

##### Testing calculate_musiplectic_technique
##### Remake for the refactored code:

plucking_techs = [
    'finger', 'pick_up', 'pick_down', 'slap', 'pop', 'tap', 'double_thumb',
    'double_thumb_downstroke', 'double_thumb_upstroke'
]

palm_mutes = [False, True]
dn_h_ah_s = [None, 'dead-note', 'natural-harmonic', ArtificialHarmonic(2, 32)]

testing_params_p_techs = []
testing_params_p_mods = []
testing_params_f_mods = []

for p_tech in plucking_techs:
    for palm_mute in palm_mutes:
        for dn_h_ah in dn_h_ah_s:
            print(p_tech)
            print(palm_mute)
            print(dn_h_ah)

            testing_params_p_techs.append(p_tech)

            ah = None
            if isinstance(dn_h_ah, ArtificialHarmonic):
                ah = dn_h_ah

            dn_h = 'fretting'
            if dn_h_ah == 'natural-harmonic':
                dn_h = 'natural-harmonic'
            elif dn_h_ah == 'dead-note':
                dn_h = 'dead-note'

            testing_params_p_mods.append(PluckingModification(palm_mute, ah))
            testing_params_f_mods.append(FrettingModification(dn_h, False))

print(testing_params_p_techs)
print(testing_params_p_mods)
print(testing_params_f_mods)

for p_tech, p_mod, f_mod in zip(testing_params_p_techs, testing_params_p_mods,
                                testing_params_f_mods):

    plucking = PluckingAdornment(
        technique=p_tech, modification=p_mod, accent=False)
    modulation = Modulation(None, None, None, None)
    fretting = FrettingAdornment(
        technique=None,
        modification=f_mod,
        accent=False,
        modulation=modulation)
    grace_note = None
    ghost_note = False
    dummy_adornment = Adornment(
        plucking=plucking,
        fretting=fretting,
        grace_note=grace_note,
        ghost_note=ghost_note)

    answer = []
    if p_tech == 'finger':
        if p_mod.palm_mute:
            answer.append('palm_mute_pluck')
            if f_mod.type == 'dead-note':
                answer.append('dead_note_pluck_pick')
            elif f_mod.type == 'natural-harmonic':
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('artificial_harmonic')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_pluck_pick')
        elif f_mod.type == 'natural-harmonic':
            answer.append('2_finger_pluck')
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('2_finger_pluck')
            answer.append('artificial_harmonic')
        else:
            answer.append('2_finger_pluck')

    if p_tech == 'pick_up' or p_tech == 'pick_down' or p_tech == 'pick':
        if p_mod.palm_mute:
            answer.append('palm_mute_pick')
            if f_mod.type == 'dead-note':
                answer.append('dead_note_pluck_pick')
            elif f_mod.type == 'natural-harmonic':
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('artificial_harmonic')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_pluck_pick')
        elif f_mod.type == 'natural-harmonic':
            answer.append('pick')
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('pick')
            answer.append('artificial_harmonic')
        else:
            answer.append('pick')

    if p_tech == 'slap':
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('dead_note_slap')
                answer.append('palm_mute_thumb_pluck')
            elif f_mod.type == 'natural-harmonic':
                answer.append('slap')
                answer.append('palm_mute_thumb_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('slap')
                answer.append('palm_mute_thumb_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('slap')
                answer.append('palm_mute_thumb_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_slap')
        elif f_mod.type == 'natural-harmonic':
            answer.append('slap')
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('slap')
            answer.append('artificial_harmonic')
        else:
            answer.append('slap')

    if p_tech == 'pop':
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_pluck')
                answer.append('dead_note_pop')
            elif f_mod.type == 'natural-harmonic':
                answer.append('pop')
                answer.append('palm_mute_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('pop')
                answer.append('palm_mute_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('pop')
                answer.append('palm_mute_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_pop')
        elif f_mod.type == 'natural-harmonic':
            answer.append('pop')
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('pop')
            answer.append('artificial_harmonic')
        else:
            answer.append('pop')

    if p_tech == 'tap':
        answer.append('tap')
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_pluck')
                answer.append('dead_note_pluck_pick')
            elif f_mod.type == 'natural-harmonic':
                answer.append('palm_mute_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('palm_mute_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('palm_mute_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_pluck_pick')
        elif f_mod.type == 'natural-harmonic':
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('artificial_harmonic')

    if p_tech == 'double_thumb':
        answer.append('double_thumb')
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_thumb_pluck')
                answer.append('dead_note_slap')
            elif f_mod.type == 'natural-harmonic':
                answer.append('palm_mute_thumb_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('palm_mute_thumb_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('palm_mute_thumb_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_slap')
        elif f_mod.type == 'natural-harmonic':
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('artificial_harmonic')

    if p_tech == 'double_thumb_downstroke':
        answer.append('double_thumb_downstroke')
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_thumb_pluck')
                answer.append('dead_note_slap')
            elif f_mod.type == 'natural-harmonic':
                answer.append('palm_mute_thumb_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('palm_mute_thumb_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('palm_mute_thumb_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_slap')
        elif f_mod.type == 'natural-harmonic':
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('artificial_harmonic')

    if p_tech == 'double_thumb_upstroke':
        answer.append('double_thumb_upstroke')
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_thumb_pluck')
                answer.append('dead_note_slap')
            elif f_mod.type == 'natural-harmonic':
                answer.append('palm_mute_thumb_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('palm_mute_thumb_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('palm_mute_thumb_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_slap')
        elif f_mod.type == 'natural-harmonic':
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('artificial_harmonic')

    print(p_tech, p_mod, f_mod)
    print(answer)
    print(calculate_musiplectic_techniques(
        AdornedNote(dummy_note, dummy_adornment)))

    assert answer == calculate_musiplectic_techniques(
        AdornedNote(dummy_note,
                    dummy_adornment)), 'Musiplectic Plucking Techniques Wrong'

f_techs = ['hammer-on', 'pull-off', 'left-handed-slap']

testing_params_f_techs = []
testing_params_p_mods = []
testing_params_f_mods = []

for f_tech in f_techs:
    for palm_mute in palm_mutes:
        for dn_h_ah in dn_h_ah_s:
            testing_params_f_techs.append(f_tech)
            ah = None

            if isinstance(dn_h_ah, ArtificialHarmonic):
                ah = dn_h_ah

            dn_h = 'fretting'
            if dn_h_ah == 'natural-harmonic':
                dn_h = 'natural-harmonic'
            elif dn_h_ah == 'dead-note':
                dn_h = 'dead-note'

            testing_params_p_mods.append(PluckingModification(palm_mute, ah))
            testing_params_f_mods.append(FrettingModification(dn_h, False))

for f_tech, p_mod, f_mod in zip(testing_params_f_techs, testing_params_p_mods,
                                testing_params_f_mods):
    plucking = PluckingAdornment(
        technique='finger', modification=p_mod, accent=False)
    modulation = Modulation(None, None, None, None)
    fretting = FrettingAdornment(
        technique=f_tech,
        modification=f_mod,
        accent=False,
        modulation=modulation)
    grace_note = None
    ghost_note = False
    dummy_adornment = Adornment(
        plucking=plucking,
        fretting=fretting,
        grace_note=grace_note,
        ghost_note=ghost_note)

    answer = []

    if f_tech == 'hammer-on':
        answer.append('hammer_on')
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_pluck')
                answer.append('dead_note_pluck_pick')
            elif f_mod.type == 'natural-harmonic':
                answer.append('palm_mute_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('palm_mute_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('palm_mute_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_pluck_pick')
        elif f_mod.type == 'natural-harmonic':
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('artificial_harmonic')

    if f_tech == 'pull-off':
        answer.append('pull_off')
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_pluck')
                answer.append('dead_note_pluck_pick')
            elif f_mod.type == 'natural-harmonic':
                answer.append('palm_mute_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('palm_mute_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('palm_mute_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_pluck_pick')
        elif f_mod.type == 'natural-harmonic':
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('artificial_harmonic')

    if f_tech == 'left-handed-slap':
        answer.append('fretting_slap')
        if p_mod.palm_mute:
            if f_mod.type == 'dead-note':
                answer.append('palm_mute_pluck')
                answer.append('dead_note_slap')
            elif f_mod.type == 'natural-harmonic':
                answer.append('palm_mute_pluck')
                answer.append('natural_harmonic')
            elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
                answer.append('palm_mute_pluck')
                answer.append('artificial_harmonic')
            else:
                answer.append('palm_mute_pluck')

        elif f_mod.type == 'dead-note':
            answer.append('dead_note_slap')
        elif f_mod.type == 'natural-harmonic':
            answer.append('natural_harmonic')
        elif isinstance(p_mod.artificial_harmonic, ArtificialHarmonic):
            answer.append('artificial_harmonic')

    print(f_tech, p_mod, f_mod)
    print(answer)
    print(calculate_musiplectic_techniques(
        AdornedNote(dummy_note, dummy_adornment)))
    assert answer == calculate_musiplectic_techniques(
        AdornedNote(dummy_note,
                    dummy_adornment)), 'Musiplectic Fretting Techniques Wrong'

assert calculate_musiplectic_dynamic(dummy_adorned_note) == [
    "ff", "cresc"
], "calculate_musiplectic_dynamic is wrong"

p_tech = 'finger'
p_mod = None

f_tech = None
f_mod = None
grace_note = None
ghost_note = False
plucking = PluckingAdornment(
    technique=p_tech, modification=p_mod, accent=False)

modulations = [
    Modulation(bend=None, vibrato=None, trill=None, slide=None),
    Modulation(
        bend=Bend('type', 25, [BendPoint(0.0, 0, False), BendPoint(6.0, 0.5, False), BendPoint(12.0, 1, False)]), vibrato=False, trill=None, slide=None),
    Modulation(
        bend=Bend('type', 50, [BendPoint(0.0, 0, False), BendPoint(6.0, 0.5, False), BendPoint(12.0, 1, False)]), vibrato=False, trill=None, slide=None),
    Modulation(
        bend=Bend('type', 100, [BendPoint(0.0, 0, False), BendPoint(6.0, 0.5, False), BendPoint(12.0, 1, False)]), vibrato=False, trill=None, slide=None),
    Modulation(
        bend=Bend('type', 25, [BendPoint(0.0, 0, True), BendPoint(6.0, 0.5, True), BendPoint(12.0, 1, True)]), vibrato=False, trill=None, slide=None),
    Modulation(
        bend=Bend('type', 50, [BendPoint(0.0, 0, True), BendPoint(6.0, 0.5, True), BendPoint(12.0, 1, True)]), vibrato=False, trill=None, slide=None),
    Modulation(
        bend=Bend('type', 100, [BendPoint(0.0, 0, True), BendPoint(6.0, 0.5, True), BendPoint(12.0, 1, True)]), vibrato=False, trill=None, slide=None),
    Modulation(bend=None, vibrato=True, trill=None, slide=None),
    Modulation(
        bend=None,
        vibrato=False,
        trill=Trill('fret', 'notated_duration'),
        slide=None),
    Modulation(
        bend=None, vibrato=False, trill=None, slide=Slide('into', 'outto')),
    Modulation(
        bend=None, vibrato=True, trill=None, slide=Slide('into', 'outto')),
    Modulation(
        bend=None,
        vibrato=True,
        trill=Trill(
            5, NotatedDuration(Fraction(1, 3), False, False, Tuplet(1, 1))),
        slide=Slide('into', 'outto')),
    Modulation(
        bend=Bend('type', 100, [BendPoint(0.0, 0, True), BendPoint(6.0, 0.5, True), BendPoint(12.0, 1, True)]),
        vibrato=True,
        trill=Trill(
            5, NotatedDuration(Fraction(1, 3), False, False, Tuplet(1, 1))),
        slide=Slide('into', 'outto')),
    Modulation(
        bend=Bend('type', 100, [BendPoint(0.0, 0, False), BendPoint(6.0, 0.5, False), BendPoint(12.0, 1, False)]),
        vibrato=True,
        trill=Trill(
            5, NotatedDuration(Fraction(1, 3), False, False, Tuplet(1, 1))),
        slide=Slide('into', 'outto'))
]
expressions = [['none'], ['quater_bend'], ['half_bend'], [
    'whole_bend'
], ['quater_bend', 'vibrato'], ['half_bend', 'vibrato'], [
    'whole_bend', 'vibrato'
], ['vibrato'], ['trill'], ['slide'], ['vibrato', 'slide'], ['vibrato', 'trill', 'slide'],
               ['whole_bend', 'vibrato', 'trill',
                'slide'], ['whole_bend', 'vibrato', 'trill', 'slide']]
for mod, exp in zip(modulations, expressions):
    fretting = FrettingAdornment(
        technique=f_tech, modification=f_mod, accent=False, modulation=mod)
    dummy_adornment = Adornment(
        plucking=plucking,
        fretting=fretting,
        grace_note=grace_note,
        ghost_note=ghost_note)
    assert calculate_musiplectic_expression(
        AdornedNote(
            dummy_note,
            dummy_adornment)) == exp, ("wrong expression musiplectics codes")

for fret in range(0, 20):
    answer = '0-4'

    if fret < 5:
        answer = '0-4'
    if fret >= 5 and fret < 12:
        answer = '5-11'
    if fret >= 12 and fret < 18:
        answer = '12-17'
    if fret >= 18:
        answer = '18+'

    assert calculate_musiplectic_fret_possition(
        AdornedNote(
            update_note(dummy_note, fret_number=fret), dummy_adornment)
    ) == answer, (
        "calculate_musiplectic_fret_possition did not find %d to be in the right range"
        % fret)

p_accents = [False, True, False, True]
f_accents = [False, False, True, True]
answers = [[], ['accent'], ['staccato'], ['staccato', 'accent']]
for p_accent, f_accent, answer in zip(p_accents, f_accents, answers):
    plucking = PluckingAdornment(
        technique='finger',
        modification=PluckingModification(False, None),
        accent=p_accent)
    modulation = Modulation(None, None, None, None)
    fretting = FrettingAdornment(
        technique=None,
        modification=FrettingModification('fretting', False),
        accent=f_accent,
        modulation=modulation)
    grace_note = None
    ghost_note = False
    dummy_adornment = Adornment(
        plucking=plucking,
        fretting=fretting,
        grace_note=grace_note,
        ghost_note=ghost_note)

    print(p_accent, f_accent, answer)
    print(calculate_musiplectic_articulations(
        AdornedNote(dummy_note, dummy_adornment)))
    assert calculate_musiplectic_articulations(
        AdornedNote(dummy_note, dummy_adornment)) == answer, "Accent is wrong"

shift = [0, 0, 0, 0, 1, 0, 0, 0, 1]
pos_window = [[1], [1, 2], [1, 2, 3], [1, 2, 3, 4], [5], [5, 6], [5, 6, 7],
              [5, 6, 7, 8], [9]]

position_window = []
for fret in range(1, 10):

    shift_distance, position_window = calculate_playing_shift(
        fret, position_window=position_window, position_window_size=4)
    #print(shift_distance, position_window)
    #print(shift[fret-1], pos_window[fret-1])
    assert shift_distance == shift[fret -
                                   1] and position_window == pos_window[fret -
                                                                        1], "Playing shift calculated wrong"

for fret in range(0, 21):
    answer = '0-4'

    if fret < 5:
        answer = '0-4'
    if fret >= 5 and fret < 12:
        answer = '5-11'
    if fret >= 12 and fret < 18:
        answer = '12-17'
    if fret >= 18:
        answer = '18+'

    assert calculate_musiplectic_grace_note_fret_position(
        GraceNote(fret, 'duration', 'dynamic', 'dead_note', 'on_beat',
                  'transition')) == answer, "grace_note fret position is wrong"

adorned_note = AdornedNote(
    dummy_note,
    Adornment(
        plucking=plucking,
        fretting=fretting,
        grace_note=GraceNote(2, Fraction(1, 32), 'p', False, False, None),
        ghost_note=ghost_note))
grace_note_list = calculate_grace_note_possitions([adorned_note])

note_from_grace_note = grace_note_list[0]

assert note_from_grace_note.note.note_number == adorned_note.note.note_number - 0.5
assert note_from_grace_note.note.pitch == 45
assert note_from_grace_note.note.fret_number == adorned_note.adornment.grace_note.fret
assert note_from_grace_note.note.string_number == adorned_note.note.string_number
assert note_from_grace_note.note.string_tuning == adorned_note.note.string_tuning
assert note_from_grace_note.note.start_time == adorned_note.note.start_time - adorned_note.adornment.grace_note.duration
assert note_from_grace_note.adornment.plucking.technique == adorned_note.adornment.plucking.technique

adorned_note = AdornedNote(
    dummy_note,
    Adornment(
        plucking=plucking,
        fretting=fretting,
        grace_note=GraceNote(2, Fraction(1, 32), 'p', False, True, None),
        ghost_note=ghost_note))
grace_note_list = calculate_grace_note_possitions([adorned_note])

note_from_grace_note = grace_note_list[0]

assert note_from_grace_note.note.note_number == adorned_note.note.note_number - 0.5
assert note_from_grace_note.note.pitch == 45
assert note_from_grace_note.note.fret_number == adorned_note.adornment.grace_note.fret
assert note_from_grace_note.note.string_number == adorned_note.note.string_number
assert note_from_grace_note.note.string_tuning == adorned_note.note.string_tuning
assert note_from_grace_note.note.start_time == adorned_note.note.start_time, "Grace note on beat start_time wrong"
assert grace_note_list[
    1].note.duration == adorned_note.note.duration - note_from_grace_note.note.duration, "main note duration is wrong"
assert grace_note_list[
    1].note.start_time == adorned_note.note.start_time + note_from_grace_note.note.duration, "main note start_time is wrong"
assert note_from_grace_note.adornment.plucking.technique == adorned_note.adornment.plucking.technique

transitions = [None, 'hammer', 'bend', 'slide']
answers = [None, 'hammer-on', None, None]

for transition, answer in zip(transitions, answers):
    adorned_note = AdornedNote(
        dummy_note,
        Adornment(
            plucking=PluckingAdornment(
                technique='finger',
                modification=PluckingModification(True, None),
                accent=False),
            fretting=FrettingAdornment(
                technique='hammer-on',
                modification='fretting',
                accent=False,
                modulation=modulation),
            grace_note=GraceNote(
                2,
                Fraction(1, 32),
                'p',
                dead_note=True,
                on_beat=True,
                transition=transition),
            ghost_note=ghost_note))

    grace_note_list = calculate_grace_note_possitions([adorned_note])
    note_from_grace_note = grace_note_list[0]

    assert note_from_grace_note.adornment.fretting.technique == 'hammer-on', "grace_note fretting technique wrong"
    assert grace_note_list[
        1].adornment.fretting.technique == answer, "adorned_note fretting technique wrong"
    assert note_from_grace_note.adornment.plucking.modification.palm_mute, "grace_note plucking mod wrong"
    assert note_from_grace_note.adornment.fretting.modification.type == 'dead-note', "grace_note fretting mod wrong"
    assert note_from_grace_note.adornment.fretting.modulation.trill == None
    assert note_from_grace_note.adornment.fretting.modulation.vibrato == False
    if transition == "bend":
        assert isinstance(
            note_from_grace_note.adornment.fretting.modulation.bend, Bend)
        assert note_from_grace_note.adornment.fretting.modulation.vibrato == False
    if transition == "slide":
        assert isinstance(
            note_from_grace_note.adornment.fretting.modulation.slide, Slide)
    if transition == "hammer":
        assert note_from_grace_note.adornment.fretting.modulation.bend == None
        assert note_from_grace_note.adornment.fretting.modulation.slide == None

# testing an issue where modulation is replaced with FrettingModification:
grace_note_test = AdornedNote(
    note=Note(
        note_number=1,
        pitch=33,
        fret_number=5,
        string_number=4,
        string_tuning={
            1: 43,
            2: 38,
            3: 33,
            4: 28
        },
        start_time=Fraction(0, 1),
        duration=Fraction(1, 4),
        notated_duration=NotatedDuration(
            value=Fraction(1, 4),
            isDotted=False,
            isDoubleDotted=False,
            tuplet=Tuplet(number_of_notes=1, equal_to=1)),
        dynamic=Dynamic(value='fff', cres_dim=None)),
    adornment=Adornment(
        plucking=PluckingAdornment(
            technique='finger',
            modification=PluckingModification(
                palm_mute=True, artificial_harmonic=None),
            accent=False),
        fretting=FrettingAdornment(
            technique='hammer-on',
            modification=FrettingModification(type=None, let_ring=False),
            accent=False,
            modulation=Modulation(
                bend=None, vibrato=False, trill=None, slide=None)),
        grace_note=GraceNote(
            fret=5,
            duration=Fraction(1, 32),
            dynamic=Dynamic(value='mf', cres_dim=None),
            dead_note=False,
            on_beat=True,
            transition=None),
        ghost_note=False))
print(calculate_grace_note_possitions([grace_note_test]))

# test calculate_playing_complexity()

# Read in the GP5 Test file:
gp5_file = "./Adorn-o/gp5files/test_scores/calculate_playing_complexity_test.gp5"
gp5song = guitarpro.parse(gp5_file)
api_test_song = parser.API.get_functions.get_song_data(gp5song)

test_song = api_test_song[0]

input_data = api_test_song[0]
song = input_data
song_complexity = calculate_playing_complexity(
    input_data,
    song=song,
    by_bar=False,
    calculation_type='both',
    weight_set='RD',
    raw_values=False,
    use_product=True)
song_complexity_by_bar = calculate_playing_complexity(
    input_data,
    song=song,
    by_bar=True,
    calculation_type='both',
    weight_set='RD',
    raw_values=False,
    use_product=True)

bar_complexity = calculate_playing_complexity(
    api_test_song[0].measures[0],
    song=song,
    by_bar=True,
    calculation_type='both',
    weight_set='RD',
    raw_values=False,
    use_product=True)

print(song_complexity, song_complexity_by_bar, bar_complexity)
assert song_complexity == song_complexity_by_bar[1]
assert song_complexity_by_bar[1] == bar_complexity
assert song_complexity == bar_complexity

song_complexity_study = calculate_playing_complexity_study(
    song=song,
    by_bar=False,
    monophonic_only=True,
    use_geometric_mean=False,
    use_total_playing_time=False,
    log_scale_values=False,
    use_product=True)
song_complexity_by_bar_study = calculate_playing_complexity_study(
    song=song,
    by_bar=True,
    monophonic_only=True,
    use_geometric_mean=False,
    use_total_playing_time=False,
    log_scale_values=False,
    use_product=True)

print(sum(song_complexity_study[0]),
      calculate_euclidean_complexity(song_complexity_study[1]),
      sum(song_complexity_by_bar_study[0][1]),
      calculate_euclidean_complexity(song_complexity_by_bar_study[0][2]))

assert song_complexity.BGM == sum(song_complexity_study[0])
assert song_complexity_by_bar[1].BGM == sum(song_complexity_by_bar_study[0][1])
assert song_complexity.EVC == calculate_euclidean_complexity(
    song_complexity_study[1])
assert song_complexity_by_bar[1].EVC == calculate_euclidean_complexity(
    song_complexity_by_bar_study[0][2])

bgm_complexity = musiplectics.duration_complexity_polynomial(
    calculate_realtime_duration(Fraction(1, 4), 85),
    use_geometric_mean=False,
    log_scale_values=False)

evc_complexity = calculate_euclidean_complexity([
    1,
    musiplectics.duration_complexity_polynomial(
        calculate_realtime_duration(Fraction(1, 4), 85),
        use_geometric_mean=False,
        log_scale_values=False), 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0, 0, 1.0,
    0, 0, 0
])

print(bgm_complexity, evc_complexity)
