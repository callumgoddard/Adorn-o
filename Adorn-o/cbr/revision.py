from __future__ import division, print_function, absolute_import

from math import sqrt
from collections import namedtuple
from fractions import Fraction

import guitarpro

from cbr.reuse import (possible_artificial_harmonic_pitches,
                       possible_natural_harmonic_pitches)
from parser.API.datatypes import *
from parser.API.calculate_functions import (
    calculate_tied_note_durations, calculate_bars_from_note_list,
    calculate_note_pitch_artificial_harmonic, calculate_note_endtime,
    calcuate_note_is_in_measure)
from parser.API.update_functions import *
from parser.utilities import fret_2_harmonic_interval

open_string_changes = namedtuple("OpenStringChanges", ["slide", 'technique'])


def revise(input_data, revise_for_gp5=True):
    """Make sure the input notes are wellformed and the
    adornments that depend on the relationship with previous notes
    are correct.

    """

    assert isinstance(input_data, Measure) or isinstance(input_data, Song)

    if isinstance(input_data, Measure):
        input_data = revise_measure(input_data, revise_for_gp5=revise_for_gp5)

    if isinstance(input_data, Song):
        input_data = revise_song(input_data, revise_for_gp5=revise_for_gp5)

    return input_data


def revise_note_pair(current_note, previous_note, measure,
                     revise_for_gp5=True):
    """

    """

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    current_note_correct_fretting_technique, current_note_new_plucking_tech = revise_fretting_technique(
        current_note, previous_note)

    current_note_new_fretting = update_fretting_adornment(
        current_note.adornment.fretting,
        technique=current_note_correct_fretting_technique)
    assert isinstance(current_note_new_fretting, FrettingAdornment)

    current_note_new_plucking = update_plucking_adornment(
        current_note.adornment.plucking,
        technique=current_note_new_plucking_tech)
    assert isinstance(current_note_new_plucking, PluckingAdornment)

    current_note = update_adornment_in_adorned_note(
        current_note.adornment,
        current_note,
        plucking=current_note_new_plucking,
        fretting=current_note_new_fretting)

    slap_pattern = revise_slap_pop_pattern(current_note, previous_note)

    current_note_pluck_tech = update_plucking_adornment(
        current_note.adornment.plucking, technique=slap_pattern.current_note)
    assert isinstance(current_note_pluck_tech, PluckingAdornment)

    current_note = update_adornment_in_adorned_note(
        current_note.adornment, current_note, plucking=current_note_pluck_tech)

    prev_note_pluck_tech = update_plucking_adornment(
        previous_note.adornment.plucking, technique=slap_pattern.previous_note)
    assert isinstance(prev_note_pluck_tech, PluckingAdornment)
    previous_note = update_adornment_in_adorned_note(
        previous_note.adornment, previous_note, plucking=prev_note_pluck_tech)

    stroke_direction = revise_stroke_directions(current_note, previous_note,
                                                measure)
    current_note_pluck_tech = update_plucking_adornment(
        current_note.adornment.plucking,
        technique=stroke_direction.current_note)
    assert isinstance(current_note_pluck_tech, PluckingAdornment)

    current_note = update_adornment_in_adorned_note(
        current_note.adornment, current_note, plucking=current_note_pluck_tech)
    prev_note_pluck_tech = update_plucking_adornment(
        previous_note.adornment.plucking,
        technique=stroke_direction.previous_note)
    assert isinstance(prev_note_pluck_tech, PluckingAdornment)
    previous_note = update_adornment_in_adorned_note(
        previous_note.adornment, previous_note, plucking=prev_note_pluck_tech)

    prev_slide, current_slide = revise_slide_shift(current_note, previous_note)
    prev_note_fretting = update_modulation_in_fretting_adornment(
        previous_note.adornment.fretting.modulation,
        previous_note.adornment.fretting,
        slide=prev_slide)
    assert isinstance(prev_note_fretting, FrettingAdornment)
    previous_note = update_adornment_in_adorned_note(
        previous_note.adornment, previous_note, fretting=prev_note_fretting)

    cur_note_fretting = update_modulation_in_fretting_adornment(
        current_note.adornment.fretting.modulation,
        current_note.adornment.fretting,
        slide=current_slide)
    assert isinstance(cur_note_fretting, FrettingAdornment)
    current_note = update_adornment_in_adorned_note(
        current_note.adornment, current_note, fretting=cur_note_fretting)

    # correct grace note duration:
    correct_grace_note = revise_grace_note_duration(current_note, previous_note)
    current_note = update_adornment_in_adorned_note(
        current_note.adornment, current_note, grace_note=correct_grace_note)

    if revise_for_gp5:
        current_note_gp5_fretting_technique = revise_for_gp5_output(
            current_note, previous_note)
        current_note_new_fretting = update_fretting_adornment(
            current_note.adornment.fretting,
            technique=current_note_gp5_fretting_technique)
        assert isinstance(current_note_new_fretting, FrettingAdornment)
        current_note = update_adornment_in_adorned_note(
            current_note.adornment,
            current_note,
            fretting=current_note_new_fretting)

    return current_note, previous_note


def revise_end_note(current_note):
    """
    """

    if current_note.adornment.fretting.modulation.slide is not None:

        into = current_note.adornment.fretting.modulation.slide.into
        outto = current_note.adornment.fretting.modulation.slide.outto
        if current_note.adornment.fretting.modulation.slide.outto == 'slide_legato' or current_note.adornment.fretting.modulation.slide.outto == 'slide_shift_to':
            outto = None

        if current_note.note.fret_number <= 1:

            if current_note.adornment.fretting.modulation.slide.into == 'slide_from_above':
                into = None

            if current_note.adornment.fretting.modulation.slide.outto == 'slide_out_below':
                outto = None

        if into is None and outto is None:
            slide = None
        else:
            slide = Slide(into, outto)

        cur_note_fretting = update_modulation_in_fretting_adornment(
            current_note.adornment.fretting.modulation,
            current_note.adornment.fretting,
            slide=slide)
        assert isinstance(cur_note_fretting, FrettingAdornment)
        current_note = update_adornment_in_adorned_note(
            current_note.adornment, current_note, fretting=cur_note_fretting)

    return current_note


def revise_measure_transitions(measure,
                               previous_measure,
                               measure_notes=[],
                               previous_measure_notes=[],
                               revise_for_gp5=True):
    """ Check the last note of the previous measure and the first note
    of the measure are wellformed and the
    adornments that depend on the relationship with previous notes
    are correct.

    """

    assert isinstance(measure, Measure)
    assert isinstance(previous_measure, Measure)

    if measure_notes == []:
        measure_notes = calculate_tied_note_durations(measure)
    if previous_measure_notes == []:
        previous_measure_notes = calculate_tied_note_durations(
            previous_measure)

    if measure_notes == [] or previous_measure_notes == []:
        return measure, previous_measure

    current_note = measure_notes[0]
    previous_note = previous_measure_notes[-1]
    current_note, previous_note = revise_note_pair(
        current_note, previous_note, measure, revise_for_gp5=revise_for_gp5)

    # add the revised notes back into each measure:
    measure_note_number_indexes = []
    for note in measure.notes:
        if isinstance(note, AdornedNote):
            measure_note_number_indexes.append(note.note.note_number)
        elif isinstance(note, Rest):
            measure_note_number_indexes.append(note.note_number)
    #measure_note_number_indexes = map(lambda x: x.note.note_number,
    #                                measure.notes)
    current_note_index = measure_note_number_indexes.index(
        current_note.note.note_number)

    measure.notes[current_note_index] = AdornedNote(
        measure.notes[current_note_index].note, current_note.adornment)

    # add the notes/adornments back into the measure - using note numbers:
    previous_measure_note_number_indexes = []
    for note in previous_measure.notes:
        if isinstance(note, AdornedNote):
            previous_measure_note_number_indexes.append(note.note.note_number)
        elif isinstance(note, Rest):
            previous_measure_note_number_indexes.append(note.note_number)

    #previous_measure_note_number_indexes = map(lambda x: x.note.note_number,
    #                                           previous_measure.notes)
    previous_note_index = previous_measure_note_number_indexes.index(
        previous_note.note.note_number)
    previous_measure.notes[previous_note_index] = AdornedNote(
        previous_measure.notes[previous_note_index].note,
        previous_note.adornment)

    return measure, previous_measure


def revise_measure(measure, measure_notes=[], revise_for_gp5=True):
    """Make sure the measure is wellformed and the
    adornments that depend on the relationship with previous notes
    are correct.

    """
    assert isinstance(measure, Measure)

    if measure_notes == []:
        measure_notes = calculate_tied_note_durations(measure)

    # work out hammer/pull patterns and masks:
    # hp_mask = hammer_pull_mask(measure_notes)
    # hp_pattern = hammer_pull_measure_pattern(measure_notes)

    previous_note = None

    corrected_notes = []

    for current_note in measure_notes:
        """
        current_note_correct_fretting_technique = revise_fretting_technique(
            current_note, previous_note)

        current_note_new_fretting = update_fretting_in_adornment(current_note.adornment.fretting, current_note, technique=current_note_correct_fretting_technique)
        current_note = update_adornment_in_adorned_note(current_note.adornment, current_note, fretting=current_note_new_fretting)

        slap_pattern = revise_slap_pop_pattern(current_note, previous_note)

        current_note_pluck_tech = update_plucking_in_adorment(current_note.adornment.plucking, current_note, technique=slap_pattern.current_note)
        current_note = update_adornment_in_adorned_note(current_note.adornment, current_note, plucking=current_note_pluck_tech)

        prev_note_pluck_tech = update_plucking_in_adorment(previous_note.adornment.plucking, previous_note, technique=slap_pattern.previous_note)
        previous_note = update_adornment_in_adorned_note(previous_note.adornment, previous_note, plucking=prev_note_pluck_tech)

        stroke_direction = revise_stroke_directions(current_note, previous_note, measure)
        current_note_pluck_tech = update_plucking_in_adorment(current_note.adornment.plucking, current_note, technique=stroke_direction.current_note)
        current_note = update_adornment_in_adorned_note(current_note.adornment, current_note, plucking=current_note_pluck_tech)
        prev_note_pluck_tech = update_plucking_in_adorment(previous_note.adornment.plucking, previous_note, technique=stroke_direction.previous_note)
        previous_note = update_adornment_in_adorned_note(previous_note.adornment, previous_note, plucking=prev_note_pluck_tech)

        if revise_for_gp5:
            current_note_gp5_fretting_technique = revise_for_gp5_output(current_note, previous_note)
            current_note_new_fretting = update_fretting_in_adornment(current_note.adornment.fretting, current_note, technique=current_note_gp5_fretting_technique)
            current_note = update_adornment_in_adorned_note(current_note.adornment, current_note, fretting=current_note_new_fretting)
        """

        # initially adjust hammer-on and pull-offs:

        # revise the current notes harmonic position
        changes = revise_harmonic_position(current_note)

        if changes is not None:
            current_note = update_note_in_adorned_note(
                current_note.note,
                current_note,
                fret_number=changes.fret,
                string_number=changes.string)

            new_adornment = current_note.adornment

            if changes.natural_harmonic:
                if current_note.adornment.fretting.modification.type != 'natural-harmonic':
                    new_adornment = update_fretting_in_adornment(
                        current_note.adornment.fretting,
                        new_adornment,
                        modification=FrettingModification(
                            type='natural-harmonic',
                            let_ring=current_note.adornment.fretting.
                            modification.let_ring))

            if current_note.adornment.plucking.modification.artificial_harmonic != changes.artificial_harmonic:
                new_adornment = update_plucking_in_adornment(
                    current_note.adornment.plucking,
                    new_adornment,
                    modification=PluckingModification(
                        palm_mute=current_note.adornment.plucking.modification.
                        palm_mute,
                        artificial_harmonic=changes.artificial_harmonic))

            current_note = update_adorned_note(
                current_note, adornment=new_adornment)

        current_note_open_string_changes, previous_note_open_string_changes = revise_open_string_restrictions(
            current_note, previous_note, measure)

        if current_note_open_string_changes is not None:

            new_adornment = current_note.adornment
            new_adornment = update_plucking_in_adornment(
                current_note.adornment.plucking,
                new_adornment,
                technique=current_note_open_string_changes.technique)
            assert isinstance(new_adornment, Adornment)

            new_fretting = update_modulation_in_fretting_adornment(
                new_adornment.fretting.modulation,
                new_adornment.fretting,
                slide=current_note_open_string_changes.slide)
            assert isinstance(new_fretting, FrettingAdornment)

            new_adornment = update_adornment(
                new_adornment, fretting=new_fretting)

            current_note = update_adorned_note(
                current_note, adornment=new_adornment)

        if previous_note_open_string_changes is not None:

            new_adornment = previous_note.adornment
            new_adornment = update_plucking_in_adornment(
                previous_note.adornment.plucking,
                new_adornment,
                technique=previous_note_open_string_changes.technique)
            assert isinstance(new_adornment, Adornment)

            new_fretting = update_modulation_in_fretting_adornment(
                new_adornment.fretting.modulation,
                new_adornment.fretting,
                slide=previous_note_open_string_changes.slide)
            assert isinstance(new_fretting, FrettingAdornment)

            new_adornment = update_adornment(
                new_adornment, fretting=new_fretting)

            previous_note = update_adorned_note(
                previous_note, adornment=new_adornment)

        # if the current note is the first note:
        # make it the previous note and skip to the first note:
        if previous_note is None:
            previous_note = current_note
            continue

        # Revise the current and previous notes:
        current_note, previous_note = revise_note_pair(
            current_note,
            previous_note,
            measure,
            revise_for_gp5=revise_for_gp5)

        # add the previous note to the updated notes list
        # make the current note the previous note
        corrected_notes.append(previous_note)
        previous_note = current_note

    # add the last updated note to the corrected_notes list:
    if previous_note is not None:
        corrected_notes.append(previous_note)

    # add the notes/adornments back into the measure - using note numbers:
    measure_note_number_indexes = []
    for note in measure.notes:
        if isinstance(note, AdornedNote):
            measure_note_number_indexes.append(note.note.note_number)
        elif isinstance(note, Rest):
            measure_note_number_indexes.append(note.note_number)
    #measure_note_number_indexes = map(lambda x: x.note.note_number,
    #                                  measure.notes)
    for corrected_note in corrected_notes:
        # get the right note in the measure to update:
        index = measure_note_number_indexes.index(
            corrected_note.note.note_number)

        # update its adornment to be the corrected_notes one:
        adorned_note = measure.notes[index]
        new_adorned_note = AdornedNote(adorned_note.note,
                                       corrected_note.adornment)
        measure = update_note_in_measure(adorned_note, new_adorned_note,
                                         measure)

    return measure


def revise_song(song, revise_for_gp5=True):
    """

    """

    assert isinstance(song, Song)

    revised_measures = []
    previous_measure = None
    measure_count = 0

    #note_list = calculate_tied_note_durations(song)
    #notes_in_measures = calculate_bars_from_note_list(note_list, song)

    LastNote = namedtuple("LastNote",
                          ['adorned_note', 'measure', "measure_count"])
    last_note = None

    for measure in song.measures:
        measure_count += 1

        # if this measure or the previous one is only rests
        # skip to the next measure.
        if measure.meta_data.only_rests:
            revised_measures.append(previous_measure)
            previous_measure = measure
            continue

        # first measure revise it!
        if measure_count == 1:
            measure = revise_measure(measure, revise_for_gp5=revise_for_gp5)

        # no previous measure: make the measure the previous one:
        if previous_measure is None:
            previous_measure = measure
            continue

        if not previous_measure.meta_data.only_rests:
            measure, previous_measure = revise_measure_transitions(
                measure,
                previous_measure,
                #measure_notes=notes_in_measures[measure.meta_data.number - 1],
                #previous_measure_notes=notes_in_measures[
                #    previous_measure.meta_data.number - 1],
                revise_for_gp5=revise_for_gp5)

        measure = revise_measure(
            measure,  #notes_in_measures[measure.meta_data.number - 1],
            revise_for_gp5=revise_for_gp5)

        # last_note = LastNote(measure.notes[-1], measure, measure_count)
        revised_measures.append(previous_measure)
        previous_measure = measure

    # add the last measure:
    revised_measures.append(previous_measure)

    last_measure_with_notes = None
    for revised_measure in reversed(revised_measures):
        if revised_measure.meta_data.only_rests:
            continue
        if revised_measure.meta_data.only_tied_notes:
            continue
        last_measure_with_notes = revised_measure
        break

    last_note = None
    if last_measure_with_notes is not None:
        for note in reversed(last_measure_with_notes.notes):
            if isinstance(note, Rest):
                continue
            if note.adornment.plucking.technique == 'tied':
                continue
            last_note = note
            break

    # put back the measures into the song:
    measure_number_indexes = map(lambda m: m.meta_data.number, song.measures)

    for rev_m in revised_measures:
        measure_index = measure_number_indexes.index(rev_m.meta_data.number)
        song.measures[measure_index] = rev_m

    if last_note is not None:
        last_measure_index = song.measures.index(last_measure_with_notes)
        last_note_index = song.measures[last_measure_index].notes.index(
            last_note)
        song.measures[last_measure_index].notes[
            last_note_index] = revise_end_note(last_note)

    return song


def revise_grace_note_duration(current_note, previous_note):
    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    correct_grace_note = current_note.adornment.grace_note

    if correct_grace_note is not None:
        if not correct_grace_note.on_beat:
            # if the grace note duration is not greater than or equal to
            # half the previous note's make is half the previous notes:
            if not ((previous_note.note.duration /
                     current_note.adornment.grace_note.duration) >= 2):
                correct_grace_note = GraceNote(
                    fret=correct_grace_note.fret,
                    duration=Fraction(float(previous_note.note.duration)*0.5),
                    dynamic=correct_grace_note.dynamic,
                    dead_note=correct_grace_note.dead_note,
                    on_beat=correct_grace_note.on_beat,
                    transition=correct_grace_note.transition)

    return correct_grace_note


def revise_fretting_technique(current_note, previous_note):
    """Check to see the hammer-on/pull-off and return
    the correct one.

    """

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    correct_fretting_technique = current_note.adornment.fretting.technique
    current_note_new_plucking = current_note.adornment.plucking.technique

    if (current_note.adornment.fretting.technique == 'hammer-on'
            or current_note.adornment.fretting.technique == 'pull-off'):

        if current_note.note.string_number == previous_note.note.string_number:
            if current_note.note.fret_number > previous_note.note.fret_number:
                correct_fretting_technique = 'hammer-on'
            elif current_note.note.fret_number < previous_note.note.fret_number:
                correct_fretting_technique = 'pull-off'
            else:
                correct_fretting_technique = None

        # can't pull off from natural harmonic
        if (current_note.adornment.fretting.technique == 'pull-off'
                or correct_fretting_technique == 'pull-off'):
            if previous_note.adornment.fretting.modification.type == 'natural-harmonic':
                correct_fretting_technique = None

        if current_note.note.string_number != previous_note.note.string_number:
            correct_fretting_technique = None

        # remove plucking technique from hammer-ons
        if correct_fretting_technique in ['hammer-on', 'pull-off']:
            current_note_new_plucking = 'finger'

    return correct_fretting_technique, current_note_new_plucking


def revise_slide_shift(current_note, previous_note):
    """Check the expression techniques make sense

    """

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    prev_new_slide = previous_note.adornment.fretting.modulation.slide
    current_new_slide = current_note.adornment.fretting.modulation.slide

    if previous_note.adornment.fretting.modulation.slide is not None:
        previous_note_outto = previous_note.adornment.fretting.modulation.slide.outto
        previous_note_into = previous_note.adornment.fretting.modulation.slide.into

        if current_note.adornment.fretting.modulation.slide is not None:
            current_note_into = current_note.adornment.fretting.modulation.slide.into
            current_note_outto = current_note.adornment.fretting.modulation.slide.outto
        else:
            current_note_into = None
            current_note_outto = None

        if (previous_note_outto == 'slide_shift_to'
                or previous_note_outto == 'slide_legato'):

            # different strings:
            if previous_note.note.string_number != current_note.note.string_number:
                if previous_note.note.string_number > current_note.note.string_number:
                    # lower string.... update the current_note.into
                    if previous_note.note.fret_number < current_note.note.fret_number:
                        current_note_into = 'slide_from_below'
                        previous_note_outto = None
                    elif previous_note.note.fret_number > current_note.note.fret_number:
                        current_note_into = 'slide_from_above'
                        previous_note_outto = None
                    elif previous_note.note.fret_number == current_note.note.fret_number:
                        if current_note.note.fret_number != 0:
                            if previous_note.note.pitch < current_note.note.pitch:
                                current_note_into = 'slide_from_below'
                                previous_note_outto = None
                            elif (previous_note.note.pitch >
                                  current_note.note.pitch
                                  and current_note.note.fret_number > 1):
                                current_note_into = 'slide_from_above'
                                previous_note_outto = None

                            elif previous_note.note.pitch == current_note.note.pitch:
                                current_note_into = None
                                previous_note_outto = None
                            else:
                                current_note_into = None
                                previous_note_outto = None
                        else:
                            if previous_note.note.pitch < current_note.note.pitch:
                                previous_note_outto = 'slide_out_above'
                            elif previous_note.note.pitch > current_note.note.pitch:
                                current_note_into = 'slide_from_above'
                                previous_note_outto = None
                            elif previous_note.note.pitch == current_note.note.pitch:
                                current_note_into = None
                                previous_note_outto = None
                            else:
                                current_note_into = None
                                previous_note_outto = None

                elif previous_note.note.string_number < current_note.note.string_number:
                    # higher string.... update the previou_note.into
                    if previous_note.note.fret_number < current_note.note.fret_number:
                        if previous_note.note.fret_number >= 2:
                            previous_note_outto = 'slide_out_above'
                        else:
                            previous_note_outto = None
                    elif previous_note.note.fret_number > current_note.note.fret_number:
                        if previous_note.note.fret_number >= 2:
                            previous_note_outto = 'slide_out_below'
                        else:
                            previous_note_outto = None
                    elif previous_note.note.fret_number == current_note.note.fret_number:
                        if previous_note.note.fret_number != 0:
                            if previous_note.note.pitch < current_note.note.pitch:
                                previous_note_outto = 'slide_out_above'
                            elif (previous_note.note.pitch >
                                  current_note.note.pitch
                                  and previous_note.note.fret_number > 1):
                                previous_note_outto = 'slide_out_below'
                            elif previous_note.note.pitch == current_note.note.pitch:
                                previous_note_outto = None
                            else:
                                previous_note_outto = None

            else:

                if previous_note.note.fret_number == current_note.note.fret_number:
                    if previous_note.note.fret_number != 0:
                        if previous_note.note.pitch < current_note.note.pitch:
                            previous_note_outto = 'slide_out_above'
                        elif (previous_note.note.pitch >
                              current_note.note.pitch
                              and previous_note.note.fret_number > 1):
                            previous_note_outto = 'slide_out_below'
                        elif previous_note.note.pitch == current_note.note.pitch:
                            previous_note_outto = None
                        else:
                            previous_note_outto = None

        if previous_note.note.fret_number <= 1:
            if previous_note_outto == 'slide_out_below':
                previous_note_outto = None
                if (current_note.note.string_number ==
                        previous_note.note.string_number
                        and current_note.note.fret_number >
                        previous_note.note.fret_number
                        and current_note.note.fret_number >= 2):

                    current_note_into = 'slide_from_below'

            if previous_note_into == 'slide_from_above':
                previous_note_into = None

        if current_note.note.fret_number <= 1:
            if current_note_into == 'slide_from_above':
                current_note_into = None
                if previous_note.note.pitch < current_note.note.pitch:
                    previous_note_outto = 'slide_out_above'

        if previous_note_outto is None and previous_note_into is None:
            prev_new_slide = None
        else:
            prev_new_slide = datatypes.Slide(previous_note_into,
                                             previous_note_outto)

        if current_note_outto is None and current_note_into is None:
            current_new_slide = None
        else:
            current_new_slide = datatypes.Slide(current_note_into,
                                                current_note_outto)

        if calculate_note_endtime(
                previous_note) != current_note.note.start_time:
            if prev_new_slide is not None and (
                    prev_new_slide.outto == 'slide_shift_to'
                    or prev_new_slide.outto == 'slide_legato'):
                if current_note.note.pitch >= previous_note.note.pitch:
                    prev_new_slide = datatypes.Slide(previous_note_into,
                                                     'slide_out_above')
                if current_note.note.pitch < previous_note.note.pitch:
                    prev_new_slide = datatypes.Slide(previous_note_into,
                                                     'slide_out_below')

    return prev_new_slide, current_new_slide


def revise_open_string_restrictions(current_note, previous_note, measure=None):

    if measure is not None:
        assert isinstance(measure, Measure)

    current_note_open_string_changes = None
    previous_note_open_string_changes = None

    current_note_new_slide = current_note.adornment.fretting.modulation.slide
    current_note_new_pluck_technique = current_note.adornment.plucking.technique

    if current_note.adornment.fretting.modulation.slide is not None:
        current_note_outto = current_note.adornment.fretting.modulation.slide.outto
        current_note_into = current_note.adornment.fretting.modulation.slide.into
    else:
        current_note_outto = None
        current_note_into = None

    if previous_note is not None:
        previous_note_new_slide = previous_note.adornment.fretting.modulation.slide
        previous_note_new_pluck_technique = previous_note.adornment.plucking.technique

        if previous_note.adornment.fretting.modulation.slide is not None:
            print(previous_note.adornment.fretting.modulation.slide)
            previous_note_outto = previous_note.adornment.fretting.modulation.slide.outto
            previous_note_into = previous_note.adornment.fretting.modulation.slide.into
        else:
            previous_note_outto = None
            previous_note_into = None

        if previous_note.note.fret_number == 0:
            if (previous_note_outto == 'slide_legato'
                    or previous_note_outto == 'slide_shift_to'):
                if current_note.note.fret_number > 1:
                    if current_note.note.pitch < previous_note.note.pitch:
                        current_note_into = 'slide_from_above'
                    else:
                        current_note_into = 'slide_from_below'
            previous_note_outto = None
            if previous_note_into == 'slide_from_below':
                previous_note_into = None

            if previous_note_into is None and previous_note_outto is None:
                previous_note_new_slide = None
            else:
                previous_note_new_slide = datatypes.Slide(
                    previous_note_into, previous_note_outto)

            if previous_note.adornment.plucking.technique == 'tap':
                if current_note.adornment.plucking.technique != 'tap':
                    previous_note_new_pluck_technique = current_note.adornment.plucking.technique
                else:

                    if measure is not None:
                        print("Measure!")
                        # find the most common technique in the measure
                        # that isn't tap and use that for the note:
                        measure_plucking_techniques = map(
                            lambda m: m.adornment.plucking.technique,
                            measure.notes)
                        print(measure_plucking_techniques)
                        technique_counts = {}
                        for m_p_tech in measure_plucking_techniques:
                            if m_p_tech == 'tap':
                                continue
                            if m_p_tech in technique_counts:
                                technique_counts[m_p_tech] += 1
                            else:
                                technique_counts[m_p_tech] = 1

                        if technique_counts == {}:
                            previous_note_new_pluck_technique = 'finger'
                        else:
                            best_technique_and_count = []
                            for t in technique_counts.keys():
                                if best_technique_and_count == []:
                                    best_technique_and_count = [
                                        t, technique_counts[t]
                                    ]
                                elif technique_counts[t] > best_technique_and_count[1]:
                                    best_technique_and_count = [
                                        t, technique_counts[t]
                                    ]

                            previous_note_new_pluck_technique = best_technique_and_count[
                                0]

                    else:
                        previous_note_new_pluck_technique = 'finger'

            previous_note_open_string_changes = open_string_changes(
                previous_note_new_slide, previous_note_new_pluck_technique)

    if current_note.note.fret_number == 0:
        if current_note_into == 'slide_from_below':
            current_note_into = None
        if current_note_into is None and current_note_outto is None:
            current_note_new_slide = None
        else:
            current_note_new_slide = datatypes.Slide(current_note_into,
                                                     current_note_outto)

        # can't tap open string note:
        if current_note.adornment.plucking.technique == 'tap':
            if previous_note is not None:
                current_note_new_pluck_technique = previous_note.adornment.plucking.technique

        current_note_open_string_changes = open_string_changes(
            current_note_new_slide, current_note_new_pluck_technique)

    return current_note_open_string_changes, previous_note_open_string_changes


def revise_slap_pop_pattern(current_note,
                            previous_note,
                            string_crossing_threshold=1):
    """Revises the slap pop pattern for notes

    """

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    slap_pop_techinques = [
        'slap',
        'pop'  # , 'double_thumb', 'double_thumb_upstroke',
        # 'double_thumb_downstroke'
    ]

    slap_techniques = [
        'slap'  # , 'double_thumb', 'double_thumb_upstroke', 'double_thumb_downstroke'
    ]

    slap_pop_order = namedtuple("PluckingTechniqueOrder",
                                ['current_note', 'previous_note'])

    # if the notes have slap/pop techinques:
    if (current_note.adornment.plucking.technique in slap_pop_techinques and
            previous_note.adornment.plucking.technique in slap_pop_techinques):

        # check is there is a string crossing:
        string_crossing = string_crossing_check(current_note, previous_note)
        if string_crossing >= string_crossing_threshold:

            if string_crossing < 0:
                # previous_note = lower
                # current_note = high

                # see if there is a clash:
                if (previous_note.adornment.plucking.technique == 'pop'
                        and current_note.adornment.plucking.technique in
                        slap_techniques):
                    # fix the clash:
                    slap_technique = current_note.adornment.plucking.technique
                    return slap_pop_order(
                        current_note='pop', previous_note=slap_technique)

            if string_crossing > 0:
                # previous_note = higher
                # current_note = lower

                # see if there is a clash:
                if (previous_note.adornment.plucking.technique in
                        slap_techniques and
                        current_note.adornment.plucking.technique == 'pop'):
                    # fix the clash:
                    slap_technique = previous_note.adornment.plucking.technique
                    return slap_pop_order(
                        current_note=slap_technique, previous_note='pop')

    # rule not matched return the orginal techniques:
    return slap_pop_order(current_note.adornment.plucking.technique,
                          previous_note.adornment.plucking.technique)


def string_crossing_check(current_note, previous_note):
    """Check if there is a string crossing between the current
    and previous note, if there is return the crossing distance.

    Returns:

    int :
    if > 0 its a  higher string to lower string crossing
    if  < 0 its a lower string to higher string crossing

    """

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    if current_note.note.string_number == previous_note.note.string_number:
        return False
    else:
        return current_note.note.string_number - previous_note.note.string_number


def revise_stroke_directions(current_note, previous_note, measure):
    """ Adjust the picking/double thumb stroke directions
    to make sense if they do not.

    """

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)
    assert isinstance(measure, Measure)

    picking_order = namedtuple("PickOrder", ['current_note', 'previous_note'])

    up_strokes = ['pick_up', 'double_thumb_upstroke']

    down_strokes = ['pick_down', 'double_thumb_downstroke']

    pick_techniques = ['pick_up', 'pick_down']

    double_thumb_techniques = [
        'double_thumb_downstroke', 'double_thumb_upstroke'
    ]

    print("For note:", current_note)
    out = picking_order(
        current_note=current_note.adornment.plucking.technique,
        previous_note=previous_note.adornment.plucking.technique)

    # find the upbeat/downbeat order of the notes:
    measure_downbeat = Fraction(
        1, int(measure.meta_data.time_signature.split("/")[-1]))

    current_note_beat = (
        current_note.note.start_time - measure.start_time) % measure_downbeat
    previous_note_beat = (
        previous_note.note.start_time - measure.start_time) % measure_downbeat

    prev = None
    current = None

    # if alternating....
    if (current_note.adornment.plucking.technique in up_strokes
            and previous_note.adornment.plucking.technique in down_strokes
        ) or (current_note.adornment.plucking.technique in down_strokes
              and previous_note.adornment.plucking.technique in up_strokes):

        # picking_order =
        if previous_note.adornment.plucking.technique in up_strokes:
            prev = 'up'
        elif previous_note.adornment.plucking.technique in down_strokes:
            prev = 'down'

        if current_note.adornment.plucking.technique in up_strokes:
            current = 'up'
        elif current_note.adornment.plucking.technique in down_strokes:
            current = 'down'

        # only adjust if the stroke direction conflicts with
        # upbeat/downbeat order:
        if current_note_beat != 0 and previous_note_beat == 0:
            prev = 'down'
            current = 'up'

        if current_note_beat == 0 and previous_note_beat != 0:
            prev = 'up'
            current = 'down'

        order = [prev, current]

        current_tech = current_note.adornment.plucking.technique
        prev_tech = previous_note.adornment.plucking.technique
        if current_note.adornment.plucking.technique in pick_techniques:
            if order[1] == 'up':
                current_tech = "pick_up"
            elif order[1] == 'down':
                current_tech = "pick_down"
        if current_note.adornment.plucking.technique in double_thumb_techniques:
            if order[1] == 'up':
                current_tech = 'double_thumb_upstroke'
            elif order[1] == 'down':
                current_tech = 'double_thumb_downstroke'

        if previous_note.adornment.plucking.technique in pick_techniques:
            if order[0] == 'up':
                prev_tech = "pick_up"
            elif order[0] == 'down':
                prev_tech = "pick_down"
        if previous_note.adornment.plucking.technique in double_thumb_techniques:
            if order[0] == 'up':
                prev_tech = 'double_thumb_upstroke'
            elif order[0] == 'down':
                prev_tech = 'double_thumb_downstroke'

        out = picking_order(current_note=current_tech, previous_note=prev_tech)

        # string crossing?
        # make sure the strokes are alternating:
        if string_crossing_check(current_note, previous_note):
            print("crossing")
            if out.previous_note in up_strokes:
                if current_note.adornment.plucking.technique in pick_techniques:
                    current_tech = "pick_down"
                if current_note.adornment.plucking.technique in double_thumb_techniques:
                    current_tech = 'double_thumb_downstroke'

            if out.previous_note in down_strokes:
                if current_note.adornment.plucking.technique in pick_techniques:
                    current_tech = "pick_up"
                if current_note.adornment.plucking.technique in double_thumb_techniques:
                    current_tech = 'double_thumb_upstroke'

        out = picking_order(
            current_note=current_tech, previous_note=out.previous_note)

    return out


def revise_harmonic_position(current_note):
    """Update the fret and string to correctly play the harmonic
    or artificial harmonic.

    """

    changes = namedtuple(
        "NoteChanges",
        ["string", "fret", 'natural_harmonic', 'artificial_harmonic'])

    current_note_changes = None

    if current_note.adornment.fretting.modification.type == 'natural-harmonic':
        # get all possible playing positions for the harmonic:
        possible_playing_pos = possible_natural_harmonic_pitches(
            current_note.note.string_tuning).get(current_note.note.pitch)

        # find the closest fret/string to play the harmonic:
        if possible_playing_pos is not None:
            new_fretting = closest_harmonic_playing_pos(
                current_note, possible_playing_pos)

            del possible_playing_pos

            # check the pitch of the natural harmonic is the same as the
            # pitch of the note:
            harm_pitch = (current_note.note.string_tuning[new_fretting.string]
                          + fret_2_harmonic_interval[new_fretting.fret])

            if harm_pitch == current_note.note.pitch:
                current_note_changes = changes(new_fretting.string,
                                               new_fretting.fret, True, None)
            else:
                current_note_changes = changes(current_note.note.string_tuning,
                                               current_note.note.fret_number,
                                               False, None)

    if (current_note.adornment.plucking.modification.artificial_harmonic is
            not None):

        possible_ah_playing_pos = possible_artificial_harmonic_pitches(
            current_note.note.string_tuning).get(current_note.note.pitch)

        if possible_ah_playing_pos is not None:
            closest_ah = closest_harmonic_playing_pos(current_note,
                                                      possible_ah_playing_pos)
            #del possible_ah_playing_pos
            print(closest_ah)
            ah = ArtificialHarmonic(
                guitarpro.models.Octave(closest_ah.ah[0]),
                guitarpro.models.PitchClass(current_note.note.pitch))

            # check the pitch to be safe?

            ah_pitch = calculate_note_pitch_artificial_harmonic(
                current_note.note.pitch, ah)

            if ah_pitch == current_note.note.pitch:
                current_note_changes = changes(closest_ah.string,
                                               closest_ah.fret, False, ah)
            else:
                current_note_changes = changes(current_note.note.string_number,
                                               current_note.note.fret_number,
                                               False, None)

    print("Revisions needed:", current_note_changes)
    return current_note_changes


def closest_harmonic_playing_pos(current_note, harmonic_positions):
    """Find the closest harmonic playing position to the current notes
    playing position.

    """

    pos_distance = []
    for playing_pos in harmonic_positions:
        dist = sqrt(
            pow(current_note.note.string_number - playing_pos.string, 2) +
            pow(current_note.note.fret_number - playing_pos.fret, 2))
        pos_distance.append((playing_pos, dist))

    # get the distance:
    distances = (map(lambda pd: pd[1], pos_distance))
    # get the min distance index:
    min_dist_index = distances.index(min(distances))
    # return the playing position with the minimum distance:
    return pos_distance[min_dist_index][0]


def revise_for_gp5_output(current_note, previous_note):
    """Adjust the adornments to follow the gp5 file format

    """

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    fretting_technique = current_note.adornment.fretting.technique
    # if previous note == trill or if previous note == slide
    # can't have hammer-on/pull-off:
    if previous_note.adornment.fretting.modulation.trill is not None:
        fretting_technique = None
    if previous_note.adornment.fretting.modulation.slide is not None:
        fretting_technique = None

    return fretting_technique


def hammer_pull_mask(measure_notes):
    """Return a dictionary indicating what notes can have a
    hammer-on or pull-off technique applied to them, starting with
    the second note of the measure.
    """
    hammer_pull_mask = {}
    if len(measure_notes) == 1:
        return hammer_pull_mask

    for n1, n2 in zip(measure_notes[::], measure_notes[1::]):
        if (n1.note.string_number == n2.note.string_number
                and n1.note.fret_number != n2.note.fret_number):
            hammer_pull_mask[n2.note.number] = True
        else:
            hammer_pull_mask[n2.note.number] = False


def hammer_pull_measure_pattern(measure_notes):
    hammer_pull_pattern = {}
    for note in measure_notes:
        if (note.adornment.fretting.technique == 'hammer-on'
                or note.adornment.fretting.technique == 'pull-off'):
            hammer_pull_pattern[note.note.number] = True
        else:
            hammer_pull_pattern[note.note.number] = False


def adjust_hammer_on_and_pull_offs_within_a_measure(
        current_note, previous_note, hammer_pull_mask, hammer_pull_pattern):
    """ if the previous note has been assigned a hammer-on/pull-off
    but cannot be performed with the technique, and the
    current note can, and hasn't been assigned a hammer-on,pull-off
    then set the current note to be a hammer-on/pull-off
    """

    if previous_note is None:
        return current_note.adornment.fretting.technique, current_note.adornment.plucking.technique

    assert isinstance(current_note, AdornedNote)
    assert isinstance(previous_note, AdornedNote)

    previous_note_hp = hammer_pull_pattern[previous_note.note.number]
    previous_note_hp_possible = hammer_pull_mask[previous_note.note.number]

    current_note_hp_possible = hammer_pull_mask[current_note.note.number]

    current_note_fretting_technique = current_note.adornment.fretting.technique
    current_note_plucking_technique = current_note.adornment.plucking.technique
    if previous_note_hp and not previous_note_hp_possible:
        if (current_note_hp_possible
                and current_note.adornment.fretting.technique != 'hammer-on'
                and current_note.adornment.fretting.technique != 'pull-off'):

            # make current_note_fretting_technique = hammer/pull
            if current_note.note.fret_number > previous_note.note.fret_number:
                current_note_fretting_technique = 'hammer-on'
            elif current_note.note.fret_number < previous_note.note.fret_number:
                current_note_fretting_technique = 'pull-off'

    if current_note_fretting_technique in ['hammer-on', 'pull-off']:
        current_note_plucking_technique = 'finger'

    return current_note_fretting_technique, current_note_plucking_technique
