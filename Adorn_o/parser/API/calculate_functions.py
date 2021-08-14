'''
Calculate Functions
'''

# Standard library imports
from fractions import Fraction
import os
from bisect import bisect_left
from math import log, e, sqrt, floor
from operator import mul, add
from collections import namedtuple
import random

# 3rd party imports
import guitarpro
from midiutil.MidiFile import *
import pretty_midi
import matlab.engine

# Local application imports
from .update_functions import *
from .datatypes import *
from .. import utilities
from . import read_functions

from ...evaluation import musiplectics
from functools import reduce


def calculate_measure_duration(measure):
    '''Return the duration (in beats) of a measure.'''

    assert isinstance(
        measure, Measure), ("Can only calculate the duration of a Measure")
    return Fraction(
        int(measure.meta_data.time_signature.split('/')[0]),
        int(measure.meta_data.time_signature.split('/')[1]))


def calculate_measure_endtime(measure):
    '''Return the measure end time (in beats).'''

    return measure.start_time + calculate_measure_duration(measure)


def calculate_song_duration(song):
    '''Return the duration (in beats) of a song.'''

    assert isinstance(song,
                      Song), ("Can only calculate the duration of a Song")

    song_duration = 0
    for measure in song.measures:
        song_duration += calculate_measure_duration(measure)

    return song_duration


def calculate_note_endtime(note):
    '''Return the end time (in beats) for the note.'''

    if isinstance(note, AdornedNote):
        return note.note.start_time + note.note.duration
    if isinstance(note, Note) or isinstance(note, Rest):
        return note.start_time + note.duration


def calculate_note_duration(note,
                            next_event_start_time,
                            return_note_data_structure=True):
    '''
    Return the duration (in beats) of a note.

    Parameters
    ---------
    note: Note
        The note the durations is to be calculated for.

    next_event_start_time: Fraction
        The start time (in beats), of the next event after the note.

    return_note_data_structure: Boolean
        A flag to determine whether the function returns the
        duration of the note, or the note with its duration updated.

    Returns
    ------

    Fraction
        The duration (in beats) if return_note_data_structure=True
    Note
        The note with its duration (in beats) upated

    '''
    duration = next_event_start_time - note.start_time
    if return_note_data_structure:
        return note._replace(duration=duration)
    else:
        return duration


def calculate_duration_for_notes_in_measure(measure):
    '''
    Calculate the durations for all notes in the measure and return
    the measure with all notes having had their duration
    parameter updated.
    '''

    assert isinstance(
        measure,
        Measure), ("Can only calculate durations for notes in a measure")

    # Get the timings of all events from the start times of notes
    # in the measure then append the bar endtime to the event_times
    event_times = []
    for note in measure.notes:
        if isinstance(note, AdornedNote):
            # if the event time is not already added to the
            # event time list, add it:
            if note.note.start_time not in event_times:
                event_times.append(note.note.start_time)
        elif isinstance(note, Rest):
            if note.start_time not in event_times:
                event_times.append(note.start_time)

    event_times.append(calculate_measure_endtime(measure))

    # sort event times so they are in order.
    # This allows the notes to be in non-chronological order
    # and the duration calculation should still work.
    event_times = sorted(event_times)

    updated_measure = measure
    for note in measure.notes:

        # cylce through the event times,
        # find what one matches the note
        # duration is the time between the note's
        # start time and the next event time.
        event_num = 0

        if isinstance(note, AdornedNote):
            event_num = event_times.index(note.note.start_time)
            dur_note = calculate_note_duration(note.note,
                                               event_times[event_num + 1])
            if dur_note == Fraction(0, 1):
                print("Duration 0")
                print("bar: ", measure.meta_data.number)
                print(note)
            update_note_in_measure(note,
                                   update_adorned_note(note, note=dur_note),
                                   updated_measure)
        elif isinstance(note, Rest):
            event_num = event_times.index(note.start_time)
            dur_note = calculate_note_duration(note,
                                               event_times[event_num + 1])
            if dur_note == Fraction(0, 1):
                print("Duration 0")
                print("bar: ", measure.meta_data.number)
                print(note)
            update_note_in_measure(note, dur_note, updated_measure)
        '''
        for event_time in event_times:
            if isinstance(note, AdornedNote):
                if note.note.start_time == event_time:
                    dur_note = calculate_note_duration(
                        note.note, event_times[event_num + 1])

                    update_note_in_measure(
                        note, update_adorned_note(note, note=dur_note),
                        updated_measure)
                    break
            elif isinstance(note, Rest):
                if note.start_time == event_time:
                    dur_note = calculate_note_duration(
                        note, event_times[event_num + 1])
                    update_note_in_measure(note, dur_note, updated_measure)
                    break
            event_num += 1
            '''

    return updated_measure


def calculate_duration_for_notes_in_song(song):
    '''
    Calculated the note.duration for all notes in a song
    '''
    assert isinstance(song, Song), "Input is not %s" % (type(Song))

    updated_song = song

    for measure in song.measures:
        new_measure = calculate_duration_for_notes_in_measure(measure)
        updated_song = update_measure_in_song(measure, new_measure,
                                              updated_song)

    return updated_song


def calculate_measure_polyphony(measure):
    '''

    '''
    assert isinstance(measure,
                      Measure), ("Can only calculate polyphony for a measure")

    note_start_times = []
    for note in measure.notes:
        # Only check adorned notes, not rests
        if isinstance(note, AdornedNote):
            # check if the note starts at the same time as another note:
            for start_time in note_start_times:
                if start_time == note.note.start_time:
                    # the measure is polyphonic:
                    # update the monophonic flag
                    return update_measure_meta_data(measure, monophonic=False)

            # add the start time of the note to the note_start_times
            note_start_times.append(note.note.start_time)

    # If there are no notes with the same start_time found the
    # measure is monophonic thus return the measure with the flag
    # set to false.
    return update_measure_meta_data(measure, monophonic=True)


def calculate_polyphony_for_measures_in_a_song(song):
    '''
    For each measure in the song, calculate if the measure contains
    polyphony, update the measure metadata to indicate if it does or not,
    then update the measure in the song. Return the song with all
    measure's metadata updated.
    '''

    assert isinstance(song, Song), "Input is not %s" % (type(Song))
    for measure in song.measures:
        calculated_measure = calculate_measure_polyphony(measure)
        song = update_measure_in_song(measure, calculated_measure, song)
    return song


def calculate_only_tied_notes_measure(measure):
    '''
    Work out if the measure is only filled with tied_notes, update
    the metadata flag to reflect if it does or not and then return the
    measure with the updated metadata.
    '''

    assert isinstance(measure, Measure), ("Input must be a Measure datatype")

    # Flag set to false, because a measure could contain only rests
    # need to check that there are actually notes in the measure.
    contains_notes = False
    for event in measure.notes:
        # if the event is an adorned note, set contains note to true
        # then check that it is not tied
        # if it is not tied, then then set only_tied_notes to false
        # and return the updated measure.
        if isinstance(event, AdornedNote):
            contains_notes = True
            if event.adornment.plucking.technique != 'tied':
                return update_measure_meta_data(measure, only_tied_notes=False)

    # if the code reaches here, then there are either
    # only rests or only tied notes in the measure.
    # if the measure contains notes, then there are only tied notes
    # else there are no tied notes only rests.
    if contains_notes:
        return update_measure_meta_data(measure, only_tied_notes=True)
    else:
        return update_measure_meta_data(measure, only_tied_notes=False)


def calculate_only_rests_measure(measure):
    '''
    Work out if the measure is only filled with rests, update
    the metadata flag to reflect if it does or not and then return the
    measure with the updated metadata.
    '''

    assert isinstance(measure, Measure), ("Input must be a Measure datatype")

    # Check each event
    for event in measure.notes:
        # if the event is an adorned note, the bar isn't all rests
        # update the only_rests parameter to false
        if isinstance(event, AdornedNote):
            return update_measure_meta_data(measure, only_only_rests=False)

    # if no adorned notes were found, the measure must be all rests
    return update_measure_meta_data(measure, only_only_rests=True)


def calcaulate_endtime(note_or_measure):
    '''
    Calculate the time that a note ends
    '''
    if isinstance(note_or_measure, Note):
        return note_or_measure.start_time + note_or_measure.duration
    elif isinstance(note_or_measure, Measure):
        return (note_or_measure.start_time +
                note_or_measure.meta_data.time_signature)


def calculate_time_sig_denominator(timesig):
    '''
    Return the time signature denominator from a timesig string
    '''
    return int(timesig.split("/")[1])


def calculate_time_sig_numerator(timesig):
    '''
    Return the time signature numerator from a timesig string
    '''
    return int(timesig.split("/")[0])


def calculate_pitch_interval(note, previous_note):
    '''
    Calculate the interval between 2 notes.
    '''
    if isinstance(note, AdornedNote) and isinstance(previous_note,
                                                    AdornedNote):
        return abs(note.note.pitch - previous_note.note.pitch)
    if isinstance(note, Note) and isinstance(previous_note, AdornedNote):
        return abs(note.pitch - previous_note.note.pitch)
    if isinstance(note, AdornedNote) and isinstance(previous_note, Note):
        return abs(note.note.pitch - previous_note.pitch)

    return


# This ends up calling 3 different functions, one for each.
# todo: possibly make this one calculation based off of the
# individual harmonic/artificial harmonic data, but the calculation would
# be the same just in a different way.
def calculate_note_pitch(fret_number, string_number, string_tuning,
                         fretting_modification, plucking_modification):
    '''
    Calculate note pitch be it fretted, harmonic or artificial harmonic
    '''
    # Calculate the midi note value for a regular fretted note.
    midinote = calculate_note_pitch_fretted(fret_number, string_number,
                                            string_tuning)

    # check to see if the note is an harmonic or artificial harmonic
    # if so calculate the pitch with the related function
    if fretting_modification.type == "natural-harmonic":
        midinote = calculate_note_pitch_harmonic(fret_number, string_number,
                                                 string_tuning)
    elif isinstance(plucking_modification, ArtificialHarmonic):
        midinote = calculate_note_pitch_artificial_harmonic(
            midinote, plucking_modification)
    return midinote


def calculate_note_pitch_fretted(fret_number, string_number, string_tuning):
    '''
    Calculate the midi note pitch from the fret, string and tuning information
    '''
    midinote = string_tuning[string_number] + fret_number
    return midinote


def calculate_note_pitch_harmonic(fret_number, string_number, string_tuning):
    '''
    Calculates the midi note value when a note is played as a
    natural harmonic, by first finding the closest harmonic interval
    to the fret, then adjusting the midi to the correct value for the harmonic.
    '''
    if utilities.fret_2_harmonic_interval[fret_number] != 'none':
        midinote = string_tuning[string_number] + utilities.fret_2_harmonic_interval[fret_number]
        return midinote


# Adjusts the midinote to the pitch of the artificial harmonic.
def calculate_note_pitch_artificial_harmonic(midinote, artificial_harmonic):
    if artificial_harmonic is None:
        return midinote

    artificial_harmonic_octave = artificial_harmonic[0]
    artificial_harmonic_pitch = artificial_harmonic[1]

    # Get the fretted note:
    #tonic = utilities.midinumber2letter(midinote)
    # work out the interval between the fretted note and the harmonic
    # first get a list of 12 note names that starts on the tonic
    #note_name_list = utilities.reorder_note_letters_to_tonic(tonic)
    # get the index number of the artificial harmonic as the list is re-ordered
    # to start with the tonic the index number is the harmonic interval value
    #artificial_harmonic_interval = note_name_list.index(str(artificial_harmonic_pitch))

    # Get the right number of octaves up the harmonic is:
    #if artificial_harmonic_octave == guitarpro.models.Octave.none:
    #    octave_offest = 0
    #elif artificial_harmonic_octave == guitarpro.models.Octave.ottava:
    #   octave_offest = 1
    #elif artificial_harmonic_octave == guitarpro.models.Octave.quindicesima:
    #    octave_offest = 2
    #elif artificial_harmonic_octave == guitarpro.models.Octave.ottavaBassa:
    #    octave_offest = 3
    #elif artificial_harmonic_octave == guitarpro.models.Octave.ottavaBassa:
    #    octave_offest = 4

    # Adjust the MIDI Note value:
    # Add the number of semitones in a octave (12) * octave offset + interval
    return (midinote + (
        12 * calculate_artificial_harmonic_octave(artificial_harmonic_octave))
            + calculate_artificial_harmonic_interval(
                midinote, artificial_harmonic_pitch))


def calculate_artificial_harmonic_interval(midinote,
                                           artificial_harmonic_pitch):
    '''
    Calculates the artificial harmonic interval
    '''
    # Get the fretted note:
    tonic = utilities.midinumber2letter(midinote)
    # work out the interval between the fretted note and the harmonic
    # first get a list of 12 note names that starts on the tonic
    note_name_list = utilities.reorder_note_letters_to_tonic(tonic)
    # get the index number of the artificial harmonic as the list is re-ordered
    # to start with the tonic the index number is the harmonic interval value
    return note_name_list.index(str(artificial_harmonic_pitch))


def calculate_artificial_harmonic_octave(artificial_harmonic_octave):
    '''
    Calculates the artificial harmonic octave
    '''

    # Get the right number of octaves up the harmonic is:
    if artificial_harmonic_octave == guitarpro.models.Octave.none:
        return 0
    elif artificial_harmonic_octave == guitarpro.models.Octave.ottava:
        return 1
    elif artificial_harmonic_octave == guitarpro.models.Octave.quindicesima:
        return 2
    elif artificial_harmonic_octave == guitarpro.models.Octave.ottavaBassa:
        return 3
    elif artificial_harmonic_octave == guitarpro.models.Octave.ottavaBassa:
        return 4


def calculate_bars_from_note_list(note_list, song_data):

    measures_list = []

    measure_notes = []

    print("For: ", song_data.meta_data.title)

    for measure in song_data.measures:
        measure_notes = []
        print("Working out what notes are in measure: ", measure.meta_data.number)
        for adorned_note in note_list:
            if calcuate_note_is_in_measure(adorned_note, measure):
                measure_notes.append(adorned_note)
        measures_list.append(measure_notes)

    return measures_list


def calculate_midi_file_for_measure_note_list(measure_note_list,
                                              measure,
                                              midi_file_name='measure.mid',
                                              output_folder=os.getcwd()):

    assert isinstance(measure_note_list, list)
    assert isinstance(measure, Measure) or isinstance(measure, list)

    if isinstance(measure, list):
        print(measure)
        for m in measure:
            assert isinstance(m, Measure)
        list_of_measures = measure
    elif isinstance(measure, Measure):
        list_of_measures = [measure]

    mididata = None

    if midi_file_name.find(".mid") == -1:
        # split off the file extension:
        midi_file_name = midi_file_name.split('.mid')[0]

    track_name = midi_file_name
    mididata = MIDIFile(
        numTracks=1,
        removeDuplicates=True,
        deinterleave=True,
        adjust_origin=False)
    track = 0
    channel = 0
    time = 0

    mididata.addTrackName(track, time, track_name)

    # set the instrument to electric bass
    program = 33  # to set the instrument to electric finger bass.
    mididata.addProgramChange(track, channel, time, program)

    #pretty_midi 

    midi_data = pretty_midi.PrettyMIDI()
    bass = pretty_midi.Instrument(program=33)


    for measure in list_of_measures:
        time = measure.start_time - list_of_measures[0].start_time
        # add the tempo of the measure.
        mididata.addTempo(track, time, measure.meta_data.tempo)

        # set the time_sig and add it:
        time_sig = measure.meta_data.time_signature.split('/')
        numerator = 0
        denominator = 1
        # denominator needs to be a power of 2.
        # the default clocks_per_tick info:
        # "By definition there are 24 ticks in a quarter note,
        # so a metronome click per quarter note would be 24."
        # so it is set to 24.
        mididata.addTimeSignature(
            track,
            time,
            int(time_sig[numerator]),
            log(int(time_sig[denominator]), 2),
            clocks_per_tick=24)

        # Add the key signature:
        # first convert the key signature into number of

        # Set defaults:
        accidental_number = 0
        accidental_type = SHARPS
        mode = MAJOR

        if measure.meta_data.key_signature == 'CMajor':
            accidental_number = 0
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'AMinor':
            accidental_number = 0
            accidental_type = SHARPS
            mode = MINOR
        if measure.meta_data.key_signature == 'FMajor':
            accidental_number = 1
            accidental_type = FLATS
            mode = MAJOR
        if measure.meta_data.key_signature == 'DMinor':
            accidental_number = 1
            accidental_type = FLATS
            mode = MINOR
        if measure.meta_data.key_signature == 'BMajorFlat':
            accidental_number = 2
            accidental_type = FLATS
            mode = MAJOR
        if measure.meta_data.key_signature == 'GMinor':
            accidental_number = 2
            accidental_type = FLATS
            mode = MINOR
        if measure.meta_data.key_signature == 'EMajorFlat':
            accidental_number = 3
            accidental_type = FLATS
            mode = MAJOR
        if measure.meta_data.key_signature == 'CMinor':
            accidental_number = 3
            accidental_type = FLATS
            mode = MINOR
        if measure.meta_data.key_signature == 'AMajorFlat':
            accidental_number = 4
            accidental_type = FLATS
            mode = MAJOR
        if measure.meta_data.key_signature == 'FMinor':
            accidental_number = 4
            accidental_type = FLATS
            mode = MINOR
        if measure.meta_data.key_signature == 'DMajorFlat':
            accidental_number = 5
            accidental_type = FLATS
            mode = MAJOR
        if measure.meta_data.key_signature == 'BMinorFlat':
            accidental_number = 5
            accidental_type = FLATS
            mode = MINOR
        if measure.meta_data.key_signature == 'GMajorFlat':
            accidental_number = 6
            accidental_type = FLATS
            mode = MAJOR
        if measure.meta_data.key_signature == 'EMinorFlat':
            accidental_number = 6
            accidental_type = FLATS
            mode = MINOR
        if measure.meta_data.key_signature == 'CMajorFlat':
            accidental_number = 7
            accidental_type = FLATS
            mode = MAJOR
        if measure.meta_data.key_signature == 'AMinorFlat':
            accidental_number = 7
            accidental_type = FLATS
            mode = MINOR
        if measure.meta_data.key_signature == 'GMajor':
            accidental_number = 1
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'EMinor':
            accidental_number = 1
            accidental_type = SHARPS
            mode = MINOR
        if measure.meta_data.key_signature == 'DMajor':
            accidental_number = 2
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'BMinor':
            accidental_number = 2
            accidental_type = SHARPS
            mode = MINOR
        if measure.meta_data.key_signature == 'AMajor':
            accidental_number = 3
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'FMinorSharp':
            accidental_number = 3
            accidental_type = SHARPS
            mode = MINOR
        if measure.meta_data.key_signature == 'EMajor':
            accidental_number = 4
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'EMinorSharp':
            accidental_number = 4
            accidental_type = SHARPS
            mode = MINOR
        if measure.meta_data.key_signature == 'BMajor':
            accidental_number = 5
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'GMinorSharp':
            accidental_number = 5
            accidental_type = SHARPS
            mode = MINOR
        if measure.meta_data.key_signature == 'FMajorSharp':
            accidental_number = 6
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'DMinorSharp':
            accidental_number = 6
            accidental_type = SHARPS
            mode = MINOR
        if measure.meta_data.key_signature == 'CMajorSharp':
            accidental_number = 7
            accidental_type = SHARPS
            mode = MAJOR
        if measure.meta_data.key_signature == 'AMinorSharp':
            accidental_number = 7
            accidental_type = SHARPS
            mode = MINOR

        mididata.addKeySignature(track, time, accidental_number,
                                 accidental_type, mode)

    measure = list_of_measures[0]
    for adorned_note in measure_note_list:
        start_time = adorned_note.note.start_time - measure.start_time
        # Make midi note from adorned_note
        midi_note = MIDINote(
            adorned_note.note.pitch, start_time * 4,
            adorned_note.note.duration * 4,
            utilities.dynamics_inv.get(adorned_note.note.dynamic.value))
        # Add note to midi file:
        mididata.addNote(track, channel,
                         midi_note.pitch, float(midi_note.time),
                         float(midi_note.duration), midi_note.volume)

        # Pretty_midi:
        # Create a Note instance, starting at 0s and ending at .5s
        note = pretty_midi.Note(
            velocity=utilities.dynamics_inv.get(adorned_note.note.dynamic.value), 
            pitch=adorned_note.note.pitch, start=start_time * 4, 
            end= (start_time * 4 + adorned_note.note.duration * 4))
        
        # Add it to the bass instrument
        bass.notes.append(note)

    try:
        # write out the midi file:
        with open(midi_file_name + '.mid', 'wb') as binfile:
            mididata.writeFile(binfile)
            return midi_file_name + '.mid'
    except:
        print('midi files not made..')
        print('trying pretty_midi')
        try:
            midi_data.instruments.append(bass)
            midi_data.write(midi_file_name + '.mid')
            return midi_file_name + '.mid'
        except:
            return False


# TODO: Check if a note overlaps a bar so the correct
# time sig can be updated for the overlap bar
def calculate_midi_files(song_data,
                         song_name=None,
                         output_folder=os.getcwd(),
                         by_bar=True,
                         monophonic_only=True):
    """
    This calculated the midi notes and produces the
    midi files for the song_data.

    This can be a midi_file for the whole song is by_bar=False,
    or midi_files for each bar of the song is by_bar=True.
    """

    assert isinstance(song_data, Song), ('Input must be a Song API datatype')

    midi_file_list = []

    # get the track name:
    if song_name is None:
        song_name = song_data.meta_data.title

    # calculate the tied note_durations
    note_list = calculate_tied_note_durations(song_data)

    bar_list = calculate_bars_from_note_list(note_list, song_data)

    mididata = None

    if not by_bar:
        track_name = song_name
        mididata = MIDIFile(
            numTracks=1,
            removeDuplicates=True,
            deinterleave=True,
            adjust_origin=False)
        track = 0
        channel = 0
        time = 0

        mididata.addTrackName(track, time, track_name)

        # set the instrument to electric bass
        program = 33  # to set the instrument to electric finger bass.
        mididata.addProgramChange(track, channel, time, program)

    for measure in song_data.measures:
        measure_count = measure.meta_data.number
        if monophonic_only:
            # Check the measure is monophonic:
            if not measure.meta_data.monophonic:
                print("Measure %d is not monophonic and is being skipped" % (
                    measure_count))
                continue

        if by_bar:
            if len(bar_list[measure_count - 1]) == 0:
                print("Measure %d has not notes and is being skipped" % (
                    measure_count))
                continue

            # setup a new midi file:
            track_name = song_name + '_bar_' + str(measure_count)
            mididata = MIDIFile(
                numTracks=1,
                removeDuplicates=True,
                deinterleave=True,
                adjust_origin=False)
            track = 0
            channel = 0
            time = 0

            mididata.addTrackName(track, time, track_name)

            # set the instrument to electric bass
            program = 33  # to set the instrument to electric finger bass.
            mididata.addProgramChange(track, channel, time, program)

            # add the tempo of the first measure.
            mididata.addTempo(track, 0, measure.meta_data.tempo)

            time_sig = measure.meta_data.time_signature.split('/')
            numerator = 0
            denominator = 1
            # denominator needs to be a power of 2.
            # the default clocks_per_tick info:
            # "By definition there are 24 ticks in a quarter note,
            # so a metronome click per quarter note would be 24."
            # so it is set to 24.
            mididata.addTimeSignature(
                track,
                0,
                int(time_sig[numerator]),
                log(int(time_sig[denominator]), 2),
                clocks_per_tick=24)
        else:
            # add the tempo of the first measure.
            mididata.addTempo(track, measure.start_time,
                              measure.meta_data.tempo)

            time_sig = measure.meta_data.time_signature.split('/')
            numerator = 0
            denominator = 1
            # denominator needs to be a power of 2.
            # the default clocks_per_tick info:
            # "By definition there are 24 ticks in a quarter note,
            # so a metronome click per quarter note would be 24."
            # so it is set to 24.
            mididata.addTimeSignature(
                track,
                measure.start_time,
                int(time_sig[numerator]),
                log(int(time_sig[denominator]), 2),
                clocks_per_tick=24)

        # add notes to the midi file:
        for adorned_note in bar_list[measure_count - 1]:

            # if processing midi by the bar
            # set start_times to be relative to measure start_time
            # so they start at 0
            if by_bar:
                start_time = adorned_note.note.start_time - measure.start_time
            else:
                start_time = adorned_note.note.start_time

            # Make midi note from adorned_note
            midi_note = MIDINote(
                adorned_note.note.pitch, start_time * 4,
                adorned_note.note.duration * 4,
                utilities.dynamics_inv.get(adorned_note.note.dynamic.value))
            # Add note to midi file:
            mididata.addNote(track, channel, midi_note.pitch,
                             float(midi_note.time), float(midi_note.duration),
                             midi_note.volume)

        # write out the midi file:
        if by_bar:

            midifile_name = output_folder + '/' + song_name + '_bar_' + str(
                measure_count) + '.mid'

            binfile = open(midifile_name, 'wb')
            mididata.writeFile(binfile)
            binfile.close()
            midi_file_list.append(midifile_name)

    # write out the midi file:
    if not by_bar:
        midifile_name = output_folder + '/' + song_name + '.mid'
        binfile = open(midifile_name, 'wb')
        mididata.writeFile(binfile)
        binfile.close()
        midi_file_list.append(midifile_name)

    # return a list of midi_files created
    return midi_file_list


def calculate_rhy_file_for_measure(measure,
                                   rhy_file_name='measure.rhy',
                                   output_folder=os.getcwd(),
                                   convert_incompatable_time_sigs=True):
    '''

    '''
    assert isinstance(measure, Measure), "note_list not a list!"

    # get a list of note_durations and velocities
    note_durations = read_functions.read_all_note_durations(measure)
    note_velocities = read_functions.read_all_note_dynamics_as_velocities(
        measure)

    # first work out the tantum for the input
    # (smallest duration of notes)
    tantum = min(note_durations)

    # Adjust the tantum so that it every duration
    # can be represented as a multiple of the tantum
    for note_duration in sorted(note_durations):
        if (tantum.denominator % note_duration.denominator) != 0:
            tantum = Fraction(1,
                              tantum.denominator * note_duration.denominator)

    tpq = int(Fraction(1, 4) / tantum)
    if tpq == 0:
        tpq = 1

    #print('Ticks Per Quater note: %s' % tpq)

    valid_time_sigs = [
        '2/2', '3/2', '4/2', '2/4', '3/4', '4/4', '5/4', '6/4', '7/4', '3/8',
        '5/8', '6/8', '9/8', '12/8'
    ]

    equivalent_time_sigs = {'7/8': ['7/4', 2], '12/16': ['12/8', 2]}

    # default TPQ_modifer = 1 indicating no modification
    tpq_mod = 1
    bar_velocities = []

    time_sig = measure.meta_data.time_signature

    if time_sig not in valid_time_sigs and convert_incompatable_time_sigs:
        if time_sig in list(equivalent_time_sigs.keys()):
            time_sig, tpq_mod = equivalent_time_sigs.get(time_sig)
    else:
        tpq_mod = 1

    time_sig_num = str(time_sig).split('/')[0]
    time_sig_den = str(time_sig).split('/')[1]

    ticksperbar = (int(time_sig_num) * tpq * 4) / (int(time_sig_den))

    for basic_note in read_functions.read_basic_note_data(measure):

        start_time = basic_note[1]
        dynamic = basic_note[-1]

        # convert the start time into number of 1/4 notes
        # and then number of ticks per quaternote
        # and then into the position in the bar
        st = int(start_time / Fraction(1, 4) * tpq * tpq_mod) % ticksperbar
        st = st % ticksperbar
        # convert the dynamic into velocity
        # and normalise it
        vel = utilities.dynamics_inv.get(dynamic.value) / max(note_velocities)
        bar_velocities.append([st, vel])

    # Format the measure in .rhy velocity format
    measure = []
    # first fill it with 0's on each tick
    for x in range(0, int(ticksperbar)):
        measure.append(0)
    # then for every time, velocity pair write the velocity
    # into the right tick in the measure
    for time, vel in bar_velocities:
        
        measure[int(time)] = vel

    # convert to string and remove square brackets
    measure = str(measure).replace("[", "")
    measure = str(measure).replace("]", "")

    with open(rhy_file_name, 'w') as rhythm_file:

        # write time sig and ticks per quaternote values to the .rhy file.
        rhythm_file.write('T\{' + str(time_sig) + '\} # time-signature\n')
        rhythm_file.write('TPQ{' + str(tpq) + '} #ticks per quaternote\n')
        rhythm_file.write('V{' + str(measure) + '}\n')

    return rhy_file_name


def calculate_rhy_file_for_song(input_data,
                                song_name=None,
                                output_folder=os.getcwd(),
                                convert_incompatable_time_sigs=True
                                #monophonic_only=True
                                ):
    '''
    Calculate the nessasary parameters and then produce a .rhy
    file to be analysed by SynPy.
    '''

    assert isinstance(input_data, Song), ("Input isn't a Song datatype")

    # setup the rhy file:
    # rhythm_file_name = score_name + '.rhy'
    if song_name is None:
        rhythm_file_name = output_folder + '/' + input_data.meta_data.title + '.rhy'
    else:
        rhythm_file_name = output_folder + '/' + song_name + '.rhy'

    rhythm_file = open(rhythm_file_name, 'wb')

    # get a list of note_durations and velocities
    note_durations = read_functions.read_all_note_durations(input_data)
    note_velocities = read_functions.read_all_note_dynamics_as_velocities(
        input_data)

    # first work out the tantum for the input
    # (smallest duration of notes)
    tantum = min(note_durations)

    # Adjust the tantum so that it every duration
    # can be represented as a multiple of the tantum
    for note_duration in sorted(note_durations):
        if (tantum.denominator % note_duration.denominator) != 0:
            tantum = Fraction(1,
                              tantum.denominator * note_duration.denominator)

    # Work out the ticks per quarter note
    tpq = int(Fraction(1, 4) / tantum)
    # print('Ticks Per Quater note: %s' % tpq)

    valid_time_sigs = [
        '2/2', '3/2', '4/2', '2/4', '3/4', '4/4', '5/4', '6/4', '7/4', '3/8',
        '5/8', '6/8', '9/8', '12/8'
    ]

    equivalent_time_sigs = {'7/8': ['7/4', 2], '12/16': ['12/8', 2]}

    # calculate the tied note_durations
    # and get a list of notes:
    note_list = calculate_tied_note_durations(input_data)
    bar_list = calculate_bars_from_note_list(note_list, input_data)

    for measure in input_data.measures:
        measure_count = measure.meta_data.number - 1
        # default TPQ_modifer = 1 indicating no modification
        tpq_mod = 1
        bar_velocities = []

        #if monophonic_only:
        #    # Check the measure is monophonic:
        #    if not measure.meta_data.monophonic:
        #        print "Measure %d is not monophonic and is being skipped" % (measure_count+1)
        #        measure_count += 1
        #        continue
        # setup the time signature and calculate the
        # number of ticks per bar
        time_sig = input_data.measures[measure_count].meta_data.time_signature

        if time_sig not in valid_time_sigs and convert_incompatable_time_sigs:
            if time_sig in list(equivalent_time_sigs.keys()):
                time_sig, tpq_mod = equivalent_time_sigs.get(time_sig)
        else:
            tpq_mod = 1

        # else, reset things to default
        time_sig_num = str(time_sig).split('/')[0]
        time_sig_den = str(time_sig).split('/')[1]

        ticksperbar = int((int(time_sig_num) * tpq * 4) / (int(time_sig_den)))

        for adorned_note in bar_list[measure_count]:
            # convert the start time into number of 1/4 notes
            # and then number of ticks per quaternote
            # and then into the position in the bar
            st = int(adorned_note.note.start_time / Fraction(1, 4) * tpq *
                     tpq_mod) % ticksperbar
            st = st % ticksperbar
            # convert the dynamic into velocity
            # and normalise it
            vel = utilities.dynamics_inv.get(
                adorned_note.note.dynamic.value) / max(note_velocities)
            bar_velocities.append([int(st), vel])

        # Format the measure in .rhy velocity format
        measure = []
        # first fill it with 0's on each tick
        for x in range(0, ticksperbar):
            measure.append(0)
        # then for every time, velocity pair write the velocity
        # into the right tick in the measure
        for time, vel in bar_velocities:
            measure[time] = vel

        # convert to string and remove square brackets
        measure = str(measure).replace("[", "")
        measure = str(measure).replace("]", "")

        # write time sig and ticks per quaternote values to the .rhy file.
        rhythm_file.write('T{' + str(time_sig) + '} # time-signature\n')
        rhythm_file.write('TPQ{' + str(tpq) + '} #ticks per quaternote\n')
        rhythm_file.write('V{' + measure + '}\n')

    # close the file and return the file name
    rhythm_file.close()

    return str(rhythm_file_name)


###########################################
# Complexity Calulation Functions
###########################################


def calculate_realtime_duration(duration, bpm):
    '''
    Calculate the duration in terms of beats per minute.
    '''
    assert (isinstance(bpm, float)
            or isinstance(bpm, int)), ('bpm must be a number')

    # Calculate the quater note duration in milliseconds:
    quater_note_duration = float(60 / float(bpm)) * 1000
    note_duration_rt = quater_note_duration * (4 * (duration))
    return note_duration_rt


# Solved using : https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value
def calculate_closest_value(myList, myNumber, return_type='smallest'):
    """
    Returns closest value to rt_durationr from sorted_tempo_beat_rt_list

    If two numbers are equally close, return the smallest number.
    """
    assert isinstance(myList, list), "myList must be a list"

    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if return_type == 'smallest':
        if after - myNumber < myNumber - before:
            return after
        else:
            return before
    if return_type == 'largest':
        if after - myNumber < myNumber - before:
            return before
        else:
            return after

    if return_type == 'closest':
        after_dif = after - myNumber
        before_dif = myNumber - before
        if min(after_dif, before_dif) == after_dif:
            return after
        if min(after_dif, before_dif) == before_dif:
            return before


# Need to break this down to allow multiple technques to be picked up
def calculate_musiplectic_techniques(adorned_note):
    '''
    Calculates the musiplectic techniques and returns the
    ones that are relevent to the adorned_note
    as a list of techniques

    Parameters:
    ----------
    adorned_note : AdornedNote
        the adorned note to read the techniques from

    Return:
    -------
    technique : list
        list of musiplectic techniques applied to the adorned_note

    Note:
        Techniques not implemented/not identifiable by this function:
        'two_handed_tap',
        '1_finger_pluck',
        'thumb_pluck',
        'ranking',
        '3_finger_pluck',
    '''

    technique = []

    # if the note is a hammer-on convert it and the plucking modifications
    # to musiplectic technique and return them:
    if adorned_note.adornment.fretting.technique == 'hammer-on':

        technique.append('hammer_on')

        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')

        if adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')

        return technique

    # if the note is a pull-off cconvert it and the plucking modifications
    # to musiplectic technique and return them:
    if adorned_note.adornment.fretting.technique == 'pull-off':

        technique.append('pull_off')

        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')

        if adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')

        return technique

    # if the note is a tap convert it and the plucking modifications
    # to musiplectic technique and return them:
    if adorned_note.adornment.plucking.technique == 'tap':

        technique.append('tap')

        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')

        if adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')

        return technique

    # if the note is a left-hand-slap convert it
    # to musiplectic technique and return it:
    if adorned_note.adornment.fretting.technique == 'left-handed-slap':
        technique.append('fretting_slap')

        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')

        if adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_slap')

        return technique

    if (adorned_note.adornment.plucking.technique == 'finger'):

        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')

            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_pluck_pick')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')

        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('2_finger_pluck')
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('2_finger_pluck')
            technique.append('artificial_harmonic')
        else:
            technique.append('2_finger_pluck')
        return technique

    if (adorned_note.adornment.plucking.technique == 'pick_up'
            or adorned_note.adornment.plucking.technique == 'pick_down'):
        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pick')

            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_pluck_pick')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')

        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('pick')
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('pick')
            technique.append('artificial_harmonic')
        else:
            technique.append('pick')
        return technique

    if (adorned_note.adornment.plucking.technique == 'slap'):

        if adorned_note.adornment.plucking.modification.palm_mute:
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_slap')
                technique.append('palm_mute_thumb_pluck')
            elif (adorned_note.adornment.fretting.modification.type ==
                  'natural-harmonic'):
                technique.append('slap')
                technique.append('palm_mute_thumb_pluck')
                technique.append('natural_harmonic')
            elif (isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic)):
                technique.append('slap')
                technique.append('palm_mute_thumb_pluck')
                technique.append('artificial_harmonic')
            else:
                technique.append('slap')
                technique.append('palm_mute_thumb_pluck')

        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_slap')

        elif (adorned_note.adornment.fretting.modification.type ==
              'natural-harmonic'):
            technique.append('slap')
            technique.append('natural_harmonic')
        elif (isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic)):
            technique.append('slap')
            technique.append('artificial_harmonic')
        else:
            technique.append('slap')

        return technique

    if (adorned_note.adornment.plucking.technique == 'pop'):

        if adorned_note.adornment.plucking.modification.palm_mute:
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('palm_mute_pluck')
                technique.append('dead_note_pop')
            elif (adorned_note.adornment.fretting.modification.type ==
                  'natural-harmonic'):
                technique.append('pop')
                technique.append('palm_mute_pluck')
                technique.append('natural_harmonic')
            elif (isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic)):
                technique.append('pop')
                technique.append('palm_mute_pluck')
                technique.append('artificial_harmonic')
            else:
                technique.append('pop')
                technique.append('palm_mute_pluck')

        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pop')

        elif (adorned_note.adornment.fretting.modification.type ==
              'natural-harmonic'):
            technique.append('pop')
            technique.append('natural_harmonic')
        elif (isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic)):
            technique.append('pop')
            technique.append('artificial_harmonic')
        else:
            technique.append('pop')

        return technique

    if (adorned_note.adornment.plucking.technique == 'double_thumb'):
        technique.append('double_thumb')
        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_thumb_pluck')
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_slap')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')

        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_slap')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        return technique

    if (adorned_note.adornment.plucking.technique == 'double_thumb_upstroke'):
        technique.append('double_thumb_upstroke')
        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_thumb_pluck')
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_slap')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')

        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_slap')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        return technique

    if (adorned_note.adornment.plucking.technique == 'double_thumb_downstroke'
        ):
        technique.append('double_thumb_downstroke')
        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_thumb_pluck')
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_slap')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')

        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_slap')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        return technique

    if (adorned_note.adornment.plucking.technique == 'double_stop'):
        technique.append('double_stop')
        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_pluck_pick')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')
        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        return technique

    if (adorned_note.adornment.plucking.technique == '3_note_chord', ):
        technique.append('3_note_chord')
        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_pluck_pick')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')
        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        return technique

    if (adorned_note.adornment.plucking.technique == '4_note_chord', ):
        technique.append('4_note_chord')
        if adorned_note.adornment.plucking.modification.palm_mute:
            technique.append('palm_mute_pluck')
            if adorned_note.adornment.fretting.modification.type == 'dead-note':
                technique.append('dead_note_pluck_pick')
            elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                technique.append('natural_harmonic')
            elif isinstance(
                    adorned_note.adornment.plucking.modification.
                    artificial_harmonic, ArtificialHarmonic):
                technique.append('artificial_harmonic')
        elif adorned_note.adornment.fretting.modification.type == 'dead-note':
            technique.append('dead_note_pluck_pick')
        elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
            technique.append('natural_harmonic')
        elif isinstance(
                adorned_note.adornment.plucking.modification.
                artificial_harmonic, ArtificialHarmonic):
            technique.append('artificial_harmonic')
        return technique


def calculate_musiplectic_dynamic(adorned_note):
    dynamic = []
    if adorned_note.note.dynamic.value is None:
        dynamic.append('none')
    else:
        dynamic.append(adorned_note.note.dynamic.value)

    if adorned_note.note.dynamic.cres_dim is None:
        dynamic.append(None)
    else:
        dynamic.append(adorned_note.note.dynamic.cres_dim)

    return dynamic


def calculate_musiplectic_expression(adorned_note):

    expression = []
    bend = None
    bend_vib = False
    if isinstance(adorned_note.adornment.fretting.modulation.bend, Bend):
        # work out what bend:
        if adorned_note.adornment.fretting.modulation.bend.value < 50:
            expression += ['quater_bend']
        elif adorned_note.adornment.fretting.modulation.bend.value >= 50 and adorned_note.adornment.fretting.modulation.bend.value < 100:
            expression += ['half_bend']
        elif adorned_note.adornment.fretting.modulation.bend.value >= 100:
            expression += ['whole_bend']

        for bend_point in adorned_note.adornment.fretting.modulation.bend.points:
            if bend_point.vibrato:
                bend_vib = True

    # elif isinstance(adorned_note.adornment.fretting.modulation.vibrato,
    #                Vibrato):
    if adorned_note.adornment.fretting.modulation.vibrato or bend_vib:
        expression += ['vibrato']
    if isinstance(adorned_note.adornment.fretting.modulation.trill, Trill):
        expression += ['trill']
    if isinstance(adorned_note.adornment.fretting.modulation.slide, Slide):
        expression += ['slide']

    if expression == []:
        expression = ['none']

    return expression


def calculate_musiplectic_fret_possition(adorned_note):
    if adorned_note.note.fret_number < 5:
        return '0-4'
    if ((adorned_note.note.fret_number > 4)
            and (adorned_note.note.fret_number < 12)):
        return '5-11'
    if ((adorned_note.note.fret_number > 11)
            and (adorned_note.note.fret_number < 18)):
        return '12-17'
    if adorned_note.note.fret_number >= 18:
        return '18+'


def calculate_musiplectic_grace_note_fret_position(grace_note):
    if grace_note.fret < 5:
        return '0-4'
    if ((grace_note.fret > 4) and (grace_note.fret < 12)):
        return '5-11'
    if ((grace_note.fret > 11) and (grace_note.fret < 18)):
        return '12-17'
    if grace_note.fret >= 18:
        return '18+'


def calculate_musiplectics_duration(adorned_note, bpm):
    '''
    Calculate the real time duration of an adorned note
    '''
    assert isinstance(adorned_note, AdornedNote), ('Must pass an AdornedNote')

    rt_duration = calculate_realtime_duration(adorned_note.note.duration, bpm)
    duration_keys = sorted(musiplectics.duration_scores().keys())

    return calculate_closest_value(duration_keys, rt_duration)


def calculate_musiplectic_articulations(adorned_note):
    '''
    Calculates the musiplectic articulations and returns the
    ones that are relevent to the adorned_note
    as a list of articulations
    '''
    articulations = []
    if adorned_note.adornment.fretting.accent is True:
        articulations += ['staccato']
    if adorned_note.adornment.plucking.accent is True:
        articulations += ['accent']
    return articulations


"""
def calculate_musiplectic_bpm(bpm):
    bpm_keys = sorted(musiplectics.duration_scores().keys())
    return calculate_closest_value(bpm_keys, bpm)
"""


def calculate_two_handed_tapping(adorned_note, previous_adorned_note):
    '''
    Calculate if two handed tapping technique is being used.

    Two handed tapping is when both hands are tapping, thus
    when a hammer_on is followed by a tap, a tap is followed by a
    hammer_on or pull_off
    '''

    if (adorned_note.adornment.plucking.technique == 'tap' and
        (previous_adorned_note.adornment.fretting.technique == 'hammer-on'
         or previous_adorned_note.adornment.fretting.technique == 'pull-off')):
        return True

    if (previous_adorned_note.adornment.plucking.technique == 'tap'
            and (adorned_note.adornment.fretting.technique == 'hammer-on'
                 or adorned_note.adornment.fretting.technique == 'pull-off')):
        return True

    return False


def calculate_triplet_feel_note_durations(input_data):
    '''
    Calculate swing adjusted durations for every note in
    the input data.

    Note: this function needs to be called before
    calculate_tied_note_durations as the tied notes also have
    durations adjusted for the swing feel.
    '''

    assert isinstance(input_data, Song) or isinstance(
        input_data, Measure), ("Must be a Song or Measure as input")

    start_time_offset = 0

    if isinstance(input_data, Song):
        measures = input_data.measures
    if isinstance(input_data, Measure):
        measures = [input_data]

    for measure in measures:
        # set a temp measure variable to store all the changes.
        triplet_feel_measure = measure

        # if the measure does not have a triplet_feel
        # continue to the next measure.
        if measure.meta_data.triplet_feel is None:
            continue

        # Check the what the triplet_feel is
        # and update the triplet_feel_value
        elif measure.meta_data.triplet_feel == '8th':
            triplet_feel_value = Fraction(1, 8)

        elif measure.meta_data.triplet_feel == '16th':
            triplet_feel_value = Fraction(1, 16)

        # get the downbeat value from the measure time_signature:
        down_beat_value = Fraction(
            1,
            calculate_time_sig_denominator(measure.meta_data.time_signature))

        # work out the down beats start_times in the measure
        downbeats = []
        for x in range(
                0,
                calculate_time_sig_numerator(
                    measure.meta_data.time_signature)):
            downbeats += [(x * down_beat_value) + measure.start_time]
        print("downbeats: ", downbeats)

        # work out the non-adjusted start_times of the
        # notes that fall in the triplet feel and need adjusting
        triplet_feel_beats = []
        triplet_feel_beats = list(
            [x + triplet_feel_value for x in downbeats])
        print(triplet_feel_beats)

        for event in measure.notes:
            # check if the note is a rest or adorned_note

            # TODO: Update this from the adorned note code!
            if isinstance(event, Rest):
                is_note = False
                note = event

            elif isinstance(event, AdornedNote):
                # event is an adorned note:
                is_note = True
                adorned_note = event
                note = event.note

            if note.start_time in downbeats:
                # If the note is an 8th note
                # it needsto be expanded.
                if note.duration == triplet_feel_value:
                    # change the note duration to be
                    # 2/3 of twice the triplet_feel_value
                    triplet_feel_duration = (
                        Fraction(2, 3) * 2 * triplet_feel_value)

                    # no start_time is needed to be adjusted
                    if is_note:
                        # update the note, add it to the triplet feel measure
                        triplet_feel_note = update_note_in_adorned_note(
                            note, adorned_note, duration=triplet_feel_duration)
                    else:
                        triplet_feel_note = update_rest(
                            note, duration=triplet_feel_duration)

                    # update the measure
                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)

                elif note.duration > triplet_feel_value:
                    # note is longer than the triplet_feel_duration
                    # need to see if the end time hits a downbeat
                    # or a triplet beat.
                    note_end_time = (note.start_time + note.duration)

                    if note_end_time in triplet_feel_beats:
                        # then the note ends on a triplet_feel_beat
                        # work out when this triplet_beat should
                        # start and extend the duration to this time
                        triplet_beat_end_time = (
                            triplet_feel_value + note_end_time)
                        triplet_feel_start_time = (
                            triplet_beat_end_time -
                            Fraction(1, 3) * triplet_feel_value)

                        note_adjusted_duration = (
                            triplet_feel_start_time - note.start_time)

                        if is_note:
                            # Update the triplet_feel_measure with the information
                            triplet_feel_note = update_note_in_adorned_note(
                                note,
                                adorned_note,
                                duration=note_adjusted_duration)
                        else:
                            triplet_feel_note = update_rest(
                                note, duration=note_adjusted_duration)

                        # update measure
                        triplet_feel_measure = update_note_in_measure(
                            event, triplet_feel_note, triplet_feel_measure)

                    if note_end_time in downbeats:
                        # the note doesn't need its duration adjusted.
                        # as it will hit another downbeat and these do not
                        # have start_time adjustments that might effect
                        # the duration of the note.
                        continue

                # need to also adjust notes smaller than the
                # triplet_feel_value such as 16th notes, etc.
                if note.duration < triplet_feel_value:
                    # work out the ratio of the note duration
                    # to the triplet_feel_value
                    adjustment_ratio = (note.duration / triplet_feel_value)

                    triplet_feel_duration = (
                        Fraction(2, 3) * 2 * triplet_feel_value)

                    note_adjusted_duration = (
                        adjustment_ratio * triplet_feel_duration)

                    if is_note:
                        # Update the triplet_feel_measure with the information
                        triplet_feel_note = update_note_in_adorned_note(
                            note,
                            adorned_note,
                            duration=note_adjusted_duration)
                    else:
                        # Update the triplet_feel_measure with the information
                        triplet_feel_note = update_rest(
                            note, duration=note_adjusted_duration)

                    # update the triplet measure
                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)

            # If the note falls on a triplet (up) beat.
            elif note.start_time in triplet_feel_beats:
                # If the note has the same value of the triplet feel
                if note.duration == triplet_feel_value:
                    # change the note duration to be
                    # 1/3 of twice the triplet_feel_value
                    triplet_feel_duration = Fraction(
                        1, 3) * 2 * triplet_feel_value

                    # the start_time of the note also needs to
                    # be adjusted to be:
                    end_time = (note.start_time + note.duration)
                    triplet_feel_start_time = (
                        end_time - triplet_feel_duration)

                    if is_note:
                        # update if it is a note
                        triplet_feel_note = update_note_in_adorned_note(
                            note,
                            adorned_note,
                            start_time=triplet_feel_start_time,
                            duration=triplet_feel_duration)
                    else:
                        # update if it is a rest
                        triplet_feel_note = update_rest(
                            note,
                            start_time=triplet_feel_start_time,
                            duration=triplet_feel_duration)
                    # update measure
                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)

                elif note.duration > triplet_feel_value:
                    # the start_time of the adorned_note
                    # needs to be adjusted.
                    triplet_beat_end_time = (
                        triplet_feel_value + note.start_time)

                    triplet_feel_start_time = (
                        triplet_beat_end_time -
                        Fraction(1, 3) * triplet_feel_value)

                    note_adjusted_start_time = triplet_feel_start_time

                    # then work out if the note
                    # would end on a downbeat
                    note_end_time = note.start_time + note.duration
                    note_adjusted_duration = note_end_time

                    if note_end_time in downbeats:
                        # the note would end on a downbeat.
                        # the duration of the note needs to be corrected
                        # so that it will end on the downbeat
                        note_adjusted_duration = (
                            note_end_time - note_adjusted_start_time)

                    # Update the triplet_feel_measure with the information
                    if is_note:

                        triplet_feel_note = update_note_in_adorned_note(
                            note,
                            adorned_note,
                            #start_time=adorned_note_adjusted_start_time,
                            start_time=note_adjusted_start_time,
                            #duration=adorned_note_adjusted_duration)
                            duration=note_adjusted_duration)
                    else:

                        triplet_feel_note = update_rest(
                            note,
                            start_time=note_adjusted_start_time,
                            duration=note_adjusted_duration)

                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)

                elif note.duration < triplet_feel_value:
                    # work out the ratio of the note duration
                    # to the triplet_feel_value
                    adjustment_ratio = note.duration / triplet_feel_value

                    triplet_feel_duration = (
                        Fraction(1, 3) * 2 * triplet_feel_value)

                    note_adjusted_duration = (
                        adjustment_ratio * triplet_feel_duration)

                    # adjust the start time of the note:
                    triplet_beat_end_time = (
                        triplet_feel_value + note.start_time)

                    triplet_feel_start_time = (
                        triplet_beat_end_time -
                        Fraction(1, 3) * triplet_feel_value)

                    # Update the triplet_feel_measure with the information
                    if is_note:
                        triplet_feel_note = update_note_in_adorned_note(
                            note,
                            event,
                            start_time=triplet_feel_start_time,
                            duration=note_adjusted_duration)
                    else:
                        triplet_feel_note = update_rest(
                            note,
                            start_time=triplet_feel_start_time,
                            duration=note_adjusted_duration)

                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)

            else:
                # the note doesn't fall on a simple beat
                # find the downbeat and the triplet beat
                # the note starts between:

                st_closest_down_beat = calculate_closest_value(
                    downbeats, note.start_time, 'closest')
                st_closest_triplet_beat = calculate_closest_value(
                    triplet_feel_beats, note.start_time, 'closest')

                # find what part of the triplet_feel section it is in
                # either the larger, or the smaller
                # adjust the timing to be in proportion with
                # the triplet feel duration of the section.

                # work out what the new_range is in relation to
                # the older range's min/max values
                if st_closest_down_beat < st_closest_triplet_beat:
                    new_range = Fraction(2, 3) * 2 * triplet_feel_value
                    old_min = st_closest_down_beat
                    old_max = st_closest_triplet_beat
                    new_max = st_closest_down_beat + new_range
                    new_min = st_closest_down_beat

                elif st_closest_down_beat > st_closest_triplet_beat:
                    new_range = Fraction(1, 3) * 2 * triplet_feel_value
                    old_min = st_closest_triplet_beat
                    old_max = st_closest_down_beat
                    new_max = st_closest_down_beat
                    new_min = new_max - new_range

                # adjust the start_time_value:
                note_adjusted_start_time = ((
                    (note.start_time - old_min) / old_max - old_min) *
                                            (new_max - new_min) + new_min)

                # then work out if the duration needs to be adjusted:
                note_end_time = adorned_note.note.start_time + adorned_note.note.duration
                et_closest_down_beat = calculate_closest_value(
                    downbeats, note_end_time, 'closest')
                et_closest_triplet_beat = calculate_closest_value(
                    triplet_feel_beats, note_end_time, 'closest')

                # if the note ends on a downbeat:
                if note_end_time == et_closest_down_beat:
                    # correct the duration to be between the
                    # adjusted start_time and the ending downbeat
                    adjusted_note_duration = (
                        et_closest_down_beat - note_adjusted_start_time)

                    # Update the triplet_feel_measure with the information
                    if is_note:
                        triplet_feel_note = update_note_in_adorned_note(
                            note,
                            event,
                            start_time=note_adjusted_start_time,
                            duration=adjusted_note_duration)
                    else:
                        triplet_feel_note = update_rest(
                            note,
                            start_time=note_adjusted_start_time,
                            duration=adjusted_note_duration)

                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)

                # if the note ends on a triplet_beat
                elif note_end_time == et_closest_triplet_beat:
                    # adjust the triplet_beat to be the correct triplet time
                    # and recalculate the duration of the note
                    # based on the adjusted triplet time + end time
                    triplet_beat_end_time = et_closest_triplet_beat + triplet_feel_value
                    triplet_feel_start_time = (
                        triplet_beat_end_time -
                        Fraction(1, 3) * triplet_feel_value)

                    adjusted_note_duration = (
                        triplet_feel_start_time - note_adjusted_start_time)

                    # Update the triplet_feel_measure with the information
                    if is_note:
                        triplet_feel_note = update_note_in_adorned_note(
                            note,
                            event,
                            start_time=note_adjusted_start_time,
                            duration=adjusted_note_duration)
                    else:
                        triplet_feel_note = update_rest(
                            note,
                            start_time=note_adjusted_start_time,
                            duration=adjusted_note_duration)

                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)
                else:
                    # the note ends somewhere between a downbeat
                    # and a triplet beat, adjust the end_time
                    # of the note to be in the correct
                    # portion of triplet feel
                    if et_closest_down_beat < et_closest_triplet_beat:
                        new_range = Fraction(2, 3) * 2 * triplet_feel_value
                        old_min = st_closest_down_beat
                        old_max = st_closest_triplet_beat
                        new_max = st_closest_down_beat + new_range
                        new_min = st_closest_down_beat

                    elif et_closest_down_beat > et_closest_triplet_beat:
                        new_range = Fraction(1, 3) * 2 * triplet_feel_value
                        old_min = st_closest_triplet_beat
                        old_max = st_closest_down_beat
                        new_max = st_closest_down_beat
                        new_min = new_max - new_range

                    # adjust the start_time_value:
                    note_adjusted_end_time = ((
                        (note_end_time - old_min) / old_max - old_min) *
                                              (new_max - new_min) + new_min)

                    adorned_note_adjusted_duration = (
                        note_adjusted_end_time - note_adjusted_start_time)

                    # Update the triplet_feel_measure with the information
                    if is_note:
                        triplet_feel_note = update_note_in_adorned_note(
                            note,
                            event,
                            start_time=note_adjusted_start_time,
                            duration=note_adjusted_duration)
                    else:
                        triplet_feel_note = update_rest(
                            note,
                            start_time=note_adjusted_start_time,
                            duration=note_adjusted_duration)

                    triplet_feel_measure = update_note_in_measure(
                        event, triplet_feel_note, triplet_feel_measure)

        if isinstance(input_data, Song):
            # update the triplet measure into the song
            update_measure_in_song(triplet_feel_measure, measure, input_data)

        if isinstance(input_data, Measure):
            # if the input was a measure,
            # return the triplet feel measure
            return triplet_feel_measure

    return input_data


def calculate_tied_note_durations(input_data):
    '''
    Go through every note in a song/measure
    find the tied notes, and what notes they are tied to
    and combine them into a list.
    '''
    previous_notes = (0, [])
    start_time = 0
    notes = 1
    save = []
    assert isinstance(input_data, Song) or isinstance(input_data, Measure), (
        "Currently can only calculate tied note durations for Song or Measure datatypes"
    )

    if isinstance(input_data, Song):
        song = input_data
        for measure in song.measures:
            for event in measure.notes:
                # check the event is a note
                if isinstance(event, AdornedNote):
                    adorned_note = event
                    # if there are no previous notes
                    if previous_notes[notes] == []:
                        # check the note isn't tied
                        # if it is a tied note to start a song/measure
                        # this will need to be ignored.
                        if adorned_note.adornment.plucking.technique != 'tied':
                            previous_notes[notes].append(adorned_note)
                            previous_notes = (adorned_note.note.start_time,
                                              previous_notes[notes])
                    else:
                        # there are previous notes
                        # if the note is not tied
                        if adorned_note.adornment.plucking.technique != 'tied':
                            # check the start time of the note:
                            if adorned_note.note.start_time == previous_notes[
                                    start_time]:
                                # then the notes are on the same beat.
                                # add this note to previous notes
                                previous_notes[notes].append(adorned_note)
                            else:
                                # the note is on a new beat,
                                # save the previous notes to save list
                                for prev_note in previous_notes[notes]:
                                    save.append(prev_note)

                                # reset the previous notes
                                previous_notes = (adorned_note.note.start_time,
                                                  [adorned_note])

                        # if this note is a tied note,
                        # find the note that it is tied to.
                        elif adorned_note.adornment.plucking.technique == 'tied':
                            for previous_note in previous_notes[notes]:
                                if (adorned_note.note.pitch ==
                                        previous_note.note.pitch
                                        and adorned_note.note.fret_number ==
                                        previous_note.note.fret_number
                                        and adorned_note.note.string_number ==
                                        previous_note.note.string_number):
                                    # then this note is tied
                                    # to the previous note.
                                    # get the index in the previous notes list
                                    index = previous_notes[notes].index(
                                        previous_note)

                                    # work out the tied note duration
                                    tied_duration = (
                                        previous_note.note.duration +
                                        adorned_note.note.duration)

                                    # update the duration value in the note
                                    updated_tied_dur_note = (
                                        update_note_in_adorned_note(
                                            previous_note.note,
                                            previous_note,
                                            duration=tied_duration))

                                    # check the update function worked:
                                    assert tied_duration == updated_tied_dur_note.note.duration, "Tied Notes Did Not Update!"
                                    # add the note back into the
                                    # previous_notes list
                                    previous_notes[notes][
                                        index] = updated_tied_dur_note
        # no more notes so append the
        # previous notes to save and return it
        for prev_note in previous_notes[notes]:
            save.append(prev_note)
    elif isinstance(input_data, Measure):
        measure = input_data
        for event in measure.notes:
            # check the event is a note
            if isinstance(event, AdornedNote):
                adorned_note = event
                # if there are no previous notes
                if previous_notes[notes] == []:
                    # check the note isn't tied
                    # if it is a tied note to start a song/measure
                    # this will need to be ignored.
                    if adorned_note.adornment.plucking.technique != 'tied':
                        previous_notes[notes].append(adorned_note)
                        previous_notes = (adorned_note.note.start_time,
                                          previous_notes[notes])
                else:
                    # there are previous notes
                    # if the note is not tied
                    if adorned_note.adornment.plucking.technique != 'tied':
                        # check the start time of the note:
                        if adorned_note.note.start_time == previous_notes[
                                start_time]:
                            # then the notes are on the same beat.
                            # add this note to previous notes
                            previous_notes[notes].append(adorned_note)
                        else:
                            # the note is on a new beat,
                            # save the previous notes to save list
                            for prev_note in previous_notes[notes]:
                                save.append(prev_note)

                            # reset the previous notes
                            previous_notes = (adorned_note.note.start_time,
                                              [adorned_note])

                    # if this note is a tied note,
                    # find the note that it is tied to.
                    elif adorned_note.adornment.plucking.technique == 'tied':
                        for previous_note in previous_notes[notes]:
                            if (adorned_note.note.pitch ==
                                    previous_note.note.pitch
                                    and adorned_note.note.fret_number ==
                                    previous_note.note.fret_number
                                    and adorned_note.note.string_number ==
                                    previous_note.note.string_number):
                                # then this note is tied
                                # to the previous note.
                                # get the index in the previous notes list
                                index = previous_notes[notes].index(
                                    previous_note)

                                # work out the tied note duration
                                tied_duration = (previous_note.note.duration +
                                                 adorned_note.note.duration)

                                # update the duration value in the note
                                updated_tied_dur_note = (
                                    update_note_in_adorned_note(
                                        previous_note.note,
                                        previous_note,
                                        duration=tied_duration))

                                # check the update function worked:
                                assert tied_duration == updated_tied_dur_note.note.duration, "Tied Notes Did Not Update!"
                                # add the note back into the
                                # previous_notes list
                                previous_notes[notes][
                                    index] = updated_tied_dur_note
        # no more notes so append the
        # previous notes to save and return it
        for prev_note in previous_notes[notes]:
            save.append(prev_note)

    return save


def calculate_playing_shift(fret, position_window=[], position_window_size=4):
    '''
    Calculate if a shift in playing position is needed to play the adorned_note
    '''

    # reduce the position window size to account for the
    # fact that it includes the fret you start counting from.
    # and it is more a fret span.
    position_window_size = position_window_size - 1
    # fret = adorned_note.note.fret_number

    # Check the note isn't an open string
    # (as no shift is needed to play open strings)

    shift_distance = 0

    if fret == 0:
        shift_distance = 0
        return shift_distance, position_window
    else:
        # Check if the fret value is already in the possiton window:
        # and the possition window is not empty
        if position_window == []:
            # No previous notes have been played in a postion
            # so there is no shift, and the fret is
            # added to the position_window
            shift_distance = 0
            position_window.append(fret)

            return shift_distance, position_window

        else:
            if fret in position_window:
                # fret is in the window:
                shift_distance = 0
                return shift_distance, position_window
            else:

                min_window = (max(position_window) - position_window_size)
                max_window = (min(position_window) + position_window_size)

                if fret >= min_window and fret <= max_window:
                    # then the fret is in the playing window:
                    shift_distance = 0
                    if fret not in position_window:
                        position_window.append(fret)

                    return shift_distance, position_window
                else:
                    if fret > max_window:
                        # shift has occured:
                        # distance = fret - max_window:
                        shift_distance = fret - max_window
                        # reset the position window:
                        position_window = [fret]
                        return shift_distance, position_window

                    elif fret < max_window:
                        # shift has occured:
                        shift_distance = min_window - fret
                        # reset the position window:
                        position_window = [fret]
                        return shift_distance, position_window
    return shift_distance, position_window


def calcuate_note_is_in_measure(adorned_note, measure):

    if (adorned_note.note.start_time >= measure.start_time
            and adorned_note.note.start_time <
        (measure.start_time + calculate_measure_duration(measure))):
        return True
    else:
        return False


def calculate_chord_fret_relationships(chord_dict):
    '''
    Calculate the relationships between the frets of the chord
    accounting for string crossings
    return [[interval1_string_crossing_dist, interval1_fret_distance],
             ... ,
             [intervalN_string_crossing_dist, intervalN_fret_distance]
            ]
    '''

    keys = list(chord_dict.keys())

    chord_fret_relations = []

    prev_fret = None
    for key in keys:
        if prev_fret is None:
            prev_fret = [key, chord_dict.get(key)]
        else:
            # string distance:
            string_dist = key - prev_fret[0]

            # fret distance:
            fret_distance = abs(chord_dict.get(key) - prev_fret[1])

            # append to the chord_fret_relations:
            chord_fret_relations.append([string_dist, fret_distance])

    return chord_fret_relations


def calculate_lowest_fret(chord):
    string_count = len(chord)
    for fret in chord:
        if fret is not None:
            return string_count, fret
        string_count -= 1


def calculate_lowest_fret_note(current_beat_chord, current_beat_notes):
    '''
    Calculate and return the lowest pitched note in current_beat_notes
    based upon the current_beat_chord list.
    '''

    print(current_beat_chord)
    current_beat_lowest_fret = calculate_lowest_fret(current_beat_chord)
    print(current_beat_lowest_fret)
    for current_beat_note in current_beat_notes:
        if (current_beat_note.note.fret_number == current_beat_lowest_fret[1]
                and current_beat_note.note.string_number ==
                current_beat_lowest_fret[0]):
            return current_beat_note


# TODO: Possible want to avoid string tuning
# and purely work off of string crossing and fret position.
def calculate_position_pitch(adorned_note):
    '''
    Calculates the pitch of a note, based upon string tuning
    and fret location.
    '''
    return (adorned_note.note.string_tuning.get(
        adorned_note.note.string_number) + adorned_note.note.fret_number)


def calculate_banding_box(chord_dict, position_type='centroid'):
    '''
    Calculate the banding box for a chord from
    its dictionary representation.

    return a tuple containing the box position and size.

    The position will be a dictionary
    where the key is the string and the value is the fret of the
    banding box position.

    The size is a list give the [string_span, fret_span] of the
    banding box for the chord.
    '''

    # works out the string distance:
    string_span = max(chord_dict.keys()) - min(chord_dict.keys())

    # work out the fretting distance:
    fret_span = max(chord_dict.values()) - min(chord_dict.values())

    # work out position:

    if position_type == 'centroid':
        # string midpoint =
        string_midpoint = max(chord_dict.keys()) - (string_span / 2)
        # fret_midpoint =
        fret_midpoint = max(chord_dict.values()) - (fret_span / 2)

    if position_type == 'top_corner':
        # get the lowest string and the fret value:
        string_midpoint = max(chord_dict.keys())
        fret_midpoint = chord_dict.get(string_midpoint)

    return ({string_midpoint: fret_midpoint}, [string_span, fret_span])


def calculate_grace_note_possitions(note_list):
    '''

    '''
    note_list_with_grace_notes = []

    previous_note = None

    if note_list == []:
        return note_list

    for adorned_note in note_list:

        # set a updated_adorned_note to adorned_note
        updated_adorned_note = adorned_note

        # and updated_previous_note to the previous note
        if previous_note:
            updated_previous_note = previous_note

        # see if there is a grace note adornment
        # to the adorned_note:
        if adorned_note.adornment.grace_note:
            grace_note = adorned_note.adornment.grace_note
            # grace note is before the note it is attached to so
            # make it fit in between this not and the previous one.
            note_number = adorned_note.note.note_number - 0.5

            # grace_note -> note information:
            pitch = (grace_note.fret + adorned_note.note.string_tuning.get(
                adorned_note.note.string_number))
            string_number = adorned_note.note.string_number
            string_tuning = adorned_note.note.string_tuning

            duration = grace_note.duration
            notated_duration = datatypes.NotatedDuration(
                duration, False, False, datatypes.Tuplet(1, 1))

            dynamic = grace_note.dynamic

            if grace_note.on_beat:
                start_time = adorned_note.note.start_time
                # Adjust the adorned_note's duration and start_time
                # to account for the grace note
                # adjust previous note's duration:
                new_duration = updated_adorned_note.note.duration - duration

                # stop divide by zero errors:
                if new_duration <= 0:
                    if updated_adorned_note.note.duration == duration:
                        new_duration = updated_adorned_note.note.duration / 2
                        duration = duration / 2

                updated_adorned_note = update_note_in_adorned_note(
                    updated_adorned_note.note,
                    updated_adorned_note,
                    start_time=(
                        updated_adorned_note.note.start_time + duration),
                    duration=(new_duration))

            else:
                #print updated_adorned_note
                #print grace_note
                start_time = updated_adorned_note.note.start_time - duration

                if previous_note is not None:
                    # adjust previous note's duration:
                    new_duration = updated_previous_note.note.duration - duration

                    # stop divide by zero errors:
                    if new_duration <= 0:
                        if updated_previous_note.note.duration == duration:
                            new_duration = updated_previous_note.note.duration / 2
                            duration = duration / 2

                    updated_previous_note = update_note_in_adorned_note(
                        updated_previous_note.note,
                        updated_previous_note,
                        duration=new_duration)

            grace_note_note = datatypes.Note(
                note_number, pitch, grace_note.fret, string_number,
                string_tuning, start_time, duration, notated_duration, dynamic)

            assert isinstance(
                updated_adorned_note.adornment.fretting.modulation,
                Modulation), "Modulation adornment is wrong"

            # Technques and adornments.....
            fretting_technique = None

            # if the adorned note is a hammer-on/pull off.
            # apply this to the grace note.
            if (adorned_note.adornment.fretting.technique == 'hammer-on' or
                    adorned_note.adornment.fretting.technique == 'pull-off'):

                if previous_note is not None:
                    # check the previous note:
                    if previous_note.note.fret_number < grace_note.fret:
                        fretting_technique = 'hammer-on'

                    elif previous_note.note.fret_number > grace_note.fret:
                        fretting_technique = 'pull-off'
                    else:
                        fretting_technique = None

                else:
                    # no previous not so the grace note can only
                    # be a hammer-on
                    fretting_technique = 'hammer-on'

                # the adorned note will then need to have the
                # hammer-on/pull-off of its note corrected.
                new_fretting = update_fretting_in_adornment(
                    adorned_note.adornment.fretting,
                    adorned_note.adornment,
                    technique=None)

                # if wanting to apply hammr-on/pull-off also to the
                # main note uncomment this block:
                """
                if grace_note.fret > adorned_note.note.fret_number:
                    new_fretting = update_fretting_in_adornment(
                        adorned_note.adornment.fretting,
                        adorned_note.adornment,
                        technique='pull-off')
                if grace_note.fret < adorned_note.note.fret_number:
                    new_fretting = update_fretting_in_adornment(
                        adorned_note.adornment.fretting,
                        adorned_note.adornment,
                        technique='hammer-on')
                """

                updated_adorned_note = update_adornment_in_adorned_note(
                    updated_adorned_note.adornment,
                    updated_adorned_note,
                    fretting=new_fretting.fretting)

            # just a test because sometimes update functions are wrong:
            assert isinstance(
                updated_adorned_note.adornment.fretting.modulation,
                Modulation), "Modulation adornment is wrong after hammer-on"

            bend = None
            slide = None
            # need to deal with transitions:
            if grace_note.transition is not None:
                if grace_note.transition == 'hammer':
                    if grace_note.fret < adorned_note.note.fret_number:
                        # the adorned note will then be as a hammer-on
                        new_fretting = update_fretting_in_adornment(
                            adorned_note.adornment.fretting,
                            adorned_note.adornment,
                            technique='hammer-on')

                        updated_adorned_note = update_adornment_in_adorned_note(
                            updated_adorned_note.adornment,
                            updated_adorned_note,
                            fretting=new_fretting.fretting)

                    if grace_note.fret > adorned_note.note.fret_number:
                        # the adorned note will then be as a pull-off
                        new_fretting = update_fretting_in_adornment(
                            adorned_note.adornment.fretting,
                            adorned_note.adornment,
                            technique='pull-off')

                        updated_adorned_note = update_adornment_in_adorned_note(
                            updated_adorned_note.adornment,
                            updated_adorned_note,
                            fretting=new_fretting.fretting)

                if grace_note.transition == 'bend':
                    # assume the bend is to the pitch the grace note
                    # is attached to, the value is in cents,
                    # 100 cents to a semitone.
                    #value = (adorned_note.note.pitch - grace_note_note.pitch) * 100
                    # or just 1/2 a semitone
                    value = 50

                    # makes a default bend object:
                    bend = datatypes.Bend('bend_release', value, [
                        BendPoint(position=0.0, value=0.0, vibrato=False),
                        BendPoint(position=3.0, value=4.0, vibrato=False),
                        BendPoint(position=6.0, value=4.0, vibrato=False),
                        BendPoint(position=9.0, value=0.0, vibrato=False),
                        BendPoint(position=12.0, value=0.0, vibrato=False)
                    ])

                if grace_note.transition == 'slide':

                    if grace_note.fret == 0:
                        # make the slide into the main note slide from above
                        new_modulation = update_modulation(
                            updated_adorned_note.adornment.fretting.modulation,
                            slide=Slide(into='slide_from_below', outto=None))
                        updated_adorned_note = update_adornment_in_adorned_note(
                            updated_adorned_note.adornment,
                            updated_adorned_note,
                            modulation=new_modulation)
                        slide = None

                    else:
                        # legato slide to the main note.
                        slide = datatypes.Slide(None, 'slide_legato')

                    updated_adorned_note

            # playing techniques
            plucking_technique = adorned_note.adornment.plucking.technique

            fretting_modification = datatypes.FrettingModification(None, False)
            if grace_note.dead_note:
                fretting_modification = datatypes.FrettingModification(
                    'dead-note', False)

            plucking_modification = datatypes.PluckingModification(False, None)
            if adorned_note.adornment.plucking.modification.palm_mute:
                plucking_modification = datatypes.PluckingModification(
                    True, None)

            # plucking adornement: 'technique', 'modification', 'accent'
            plucking = datatypes.PluckingAdornment(
                plucking_technique, plucking_modification, False)

            # fretting adornment: 'technique', 'modification', 'accent', 'modulation'

            fretting = datatypes.FrettingAdornment(
                fretting_technique, fretting_modification, False,
                datatypes.Modulation(bend, False, None, slide))

            grace_note_adornment = datatypes.Adornment(plucking, fretting,
                                                       None, False)

            # Made the adorned_note_from_grace_note
            adorned_note_from_grace_note = datatypes.AdornedNote(
                grace_note_note, grace_note_adornment)

            if previous_note is not None:
                note_list_with_grace_notes.append(updated_previous_note)

            # add the grace note to the note list with grace notes:
            note_list_with_grace_notes.append(adorned_note_from_grace_note)

            # Set the previous note to be the updated adorned note
            # print updated_adorned_note
            previous_note = updated_adorned_note

        else:
            # no grace note:
            # add the updated previous note
            # to the note list with grace notes:
            if previous_note is not None:
                note_list_with_grace_notes.append(updated_previous_note)

            # Set the previous note to be the updated adorned note
            previous_note = updated_adorned_note

    if previous_note:
        updated_previous_note = previous_note

    # Append the last previous note:
    note_list_with_grace_notes.append(updated_previous_note)

    # return the list of notes with grace notes added
    return note_list_with_grace_notes


def calculate_playing_complexity(input_data,
                                 song=None,
                                 by_bar=True,
                                 calculation_type='both',
                                 weight_set='GMS',
                                 raw_values=False,
                                 unadorned_value=False,
                                 use_product=True):
    '''
    This calculates the complexity of the input data.

    input_data can be:
        - API.datatypes.Song
        - a measure

        in the future maybe also:
        - a list of notes,
        - or a list of measures, with a list of notes within the measure


    song = API.datatypes.Song that the input_data is from,

    by_bar can be:
        - boolean
            - True: calculate the complexity for every bar in the song
            - False: calculate the complexity for the whole song
        - list of measure numbers:
            - calculate the complexity for each measure in listed

    calculation_type:
        - 'Both' / 'both'
            - calculate the complexity using
                BGM and EVC calculations
        - 'BGM' | 'bgm'
            - calculate the complexity using
                only the BGM calculation
        - 'EVC' | 'evc'
            - calculate the complexity using
                only the EVC calculation
    weight_set:
        - specifies the complexity weight set to use out of:
            GM
            GMS
            GMT
            GMTS
            RD
            RDT

    raw_values:
        True:
            returns the individual:
                 note complexities
                 interval complexities
                 complexity vector
        False:
            returns the complexity value

    use_product:
        - if True take the product of the complexity weights
        of musical elements from the same musical group

        - if False take the sum of the complexity weights
        of musical elements from the same musical group

    '''

    # Check for the weight set:
    if weight_set == 'GM':
        use_geometric_mean = True
        use_total_playing_time = False
        log_scale_values = False
    if weight_set == 'GMS':
        use_geometric_mean = True
        use_total_playing_time = False
        log_scale_values = True
    if weight_set == 'GMT':
        use_geometric_mean = True
        use_total_playing_time = True
        log_scale_values = False
    if weight_set == 'GMTS':
        use_geometric_mean = True
        use_total_playing_time = True
        log_scale_values = False
    if weight_set == 'RD':
        use_geometric_mean = False
        use_total_playing_time = False
        log_scale_values = False
    if weight_set == 'RDT':
        use_geometric_mean = False
        use_total_playing_time = True
        log_scale_values = False

    # parameters for calculating complexity:
    position_window = []

    playing_technique_complexity = 0
    duration_tempo_complexity = 0
    key_sig_complexity = 0
    time_sig_complexity = 0
    bpm_complexity = 0
    expressive_techniques_complexity = 0
    articulations_accents_complexity = 0
    dynamics_complexity = 0
    fret_playing_postion_complexity = 0

    interval_complexity = 0
    interval_ioi_complexity = 0
    shift_distance_complexity = 0
    interval_dynamic_complexity = 0
    interval_fret_position_complexity = 0
    interval_expression_complexity = 0

    note_playing_complexities = []
    note_interval_complexities = []

    complexity_by_bar = {}

    if unadorned_value:
        playing_technique_complexity_unadorned = 0
        expressive_techniques_complexity_unadorned = 0
        articulations_accents_complexity_unadorned = 0
        dynamics_complexity_unadorned = 0

        interval_dynamic_complexity_unadorned = 0
        interval_expression_complexity_unadorned = 0

        note_interval_complexities_unadorned = []
        note_playing_complexities_unadorned = []

        complexity_by_bar_unadorned = {}

    # parameters for interval calculations
    previous_note = None

    # for output:
    BGM = namedtuple("ComplexityBGM", ["BGM"])
    EVC = namedtuple("ComplexityEVC", ['EVC'])
    Complexity = namedtuple("ComplexityBoth", ["BGM", 'EVC'])
    output_complexities = namedtuple("OutputComplexities",
                                     ["adorned", "unadorned"])

    note_list = []
    note_list_for_each_measure = []
    measures_to_process = []

    # work out what the input is:
    if isinstance(input_data, Song):
        if song is None:
            song = input_data
        else:
            print("Both song and input_data have been specified, using only input_data")
            song = input_data

        # calculated the tied note_durations
        note_list = calculate_tied_note_durations(song)

        # organise the note lists by measure
        note_list_for_each_measure = calculate_bars_from_note_list(
            note_list, song)

    if isinstance(input_data, list):
        # check if its a list of bars or a list of notes:
        if len(input_data) > 0:
            if isinstance(input_data[0], list):
                # probably a list of notes in each measure
                note_list_for_each_measure = input_data
            elif isinstance(input_data[0], AdornedNote):
                note_list = input_data

    assert (isinstance(by_bar, list) or isinstance(
        by_bar, bool)), ("by_bar must be a boolean or list of bars")

    if isinstance(by_bar, list):
        # a list of measures is specified:
        measures_to_process = by_bar
    else:
        #if by_bar is True:
        # no list is specified so make the range number of measures
        # that have note lists.
        measures_to_process = list(range(0, len(note_list_for_each_measure)))
    if isinstance(input_data, Song) or isinstance(input_data, list):
        for measure_number in measures_to_process:
            # skip non-monophonic measures:
            if song.measures[measure_number].meta_data.monophonic is False:
                '''
                if by_bar:
                    # add 1 to bar count to reflect actual count
                    # and not list indexing
                    if calculation_type == 'both':
                        complexity_by_bar[measure_number + 1] = Complexity(None, None)
                    elif calculation_type == 'BGM':
                        complexity_by_bar[measure_number + 1] = BGM(None)
                    elif calculation_type == 'EVC':
                        complexity_by_bar[measure_number + 1] = EVC(None, None)
                '''

                continue

            # measure info:
            key_sig = song.measures[measure_number].meta_data.key_signature
            time_sig = song.measures[measure_number].meta_data.time_signature

            # if the time sig doesn't have a complexity weight skip the measure
            if time_sig not in list(musiplectics.time_sig_weights().keys()):
                continue

            bpm = song.measures[measure_number].meta_data.tempo

            # add grace notes as regular notes into the measures:
            #note_list_for_each_measure[
            #    measure_number] = calculate_grace_note_possitions(
            #        note_list_for_each_measure[measure_number])

            # Need to update this......
            if note_list_for_each_measure != []:
                # add grace notes as regular notes into the measures:
                note_list_for_each_measure[
                    measure_number] = calculate_grace_note_possitions(
                        note_list_for_each_measure[measure_number])

                notelist = note_list_for_each_measure[measure_number]
            else:
                notelist = note_list

            for adorned_note in notelist:

                # Note info:
                playing_techniques = calculate_musiplectic_techniques(
                    adorned_note)
                '''
                if adorned_note.note.duration == 0:
                    if adorned_note.note.notated_duration.value != 0:
                        rt_duration = calculate_realtime_duration(
                            adorned_note.note.notated_duration.value, bpm)
                else:
                '''

                rt_duration = calculate_realtime_duration(
                    adorned_note.note.duration, bpm)
                #duration_tempo = calculate_musiplectics_duration(adorned_note, bpm)
                expressive_techniques = calculate_musiplectic_expression(
                    adorned_note)
                articulations_accents = calculate_musiplectic_articulations(
                    adorned_note)
                dynamic = calculate_musiplectic_dynamic(adorned_note)
                fret_playing_postion = calculate_musiplectic_fret_possition(
                    adorned_note)

                # calculate the complexity values from note info:

                # variable to keep track of the complexity scores for techniques
                # in this note, used to calculate the full complexity score.
                playing_technique_note_scores = []

                for playing_technique in playing_techniques:
                    # updated the playing technique complexity
                    # playing_technique_complexity += musiplectics.technique_scores(
                    # ).get(playing_technique)
                    # and add the scores to the note score list
                    playing_technique_note_scores.append(
                        musiplectics.technique_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(
                                playing_technique))

                if use_product:
                    playing_technique_complexity += reduce(
                        mul, playing_technique_note_scores)
                else:
                    playing_technique_complexity += reduce(
                        add, playing_technique_note_scores)

                duration_tempo_score = musiplectics.duration_complexity_polynomial(
                    rt_duration,
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values)
                duration_tempo_complexity += duration_tempo_score

                time_sig_score = musiplectics.time_sig_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(time_sig)

                time_sig_complexity += time_sig_score

                bpm_list = sorted(
                    musiplectics.tempo_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values)[0].keys())

                bpm_musiplectic = calculate_closest_value(bpm_list, bpm)

                bpm_score = musiplectics.tempo_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values)[0].get(
                        int(bpm_musiplectic))

                bpm_complexity += bpm_score

                expressive_techniques_score = []
                for expressive_technique in expressive_techniques:
                    expressive_techniques_score.append(
                        musiplectics.expression_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(
                                expressive_technique))

                if use_product:
                    expressive_techniques_complexity += reduce(
                        mul, expressive_techniques_score)
                else:
                    expressive_techniques_complexity += reduce(
                        add, expressive_techniques_score)

                articulations_accent_score = []

                if articulations_accents == []:
                    # articulations_accents_complexity += musiplectics.articulation_scores().get(None)
                    articulations_accent_score.append(
                        musiplectics.articulation_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(None))
                else:
                    for articulations_accent in articulations_accents:
                        # articulations_accents_complexity += musiplectics.articulation_scores().get(articulations_accent)
                        articulations_accent_score.append(
                            musiplectics.articulation_weights(
                                use_geometric_mean=use_geometric_mean,
                                use_total_playing_time=use_total_playing_time,
                                log_scale_values=log_scale_values).get(
                                    articulations_accent))

                if use_product:
                    articulations_accents_complexity += reduce(
                        mul, articulations_accent_score)
                else:
                    articulations_accents_complexity += reduce(
                        add, articulations_accent_score)

                dynamic_score = []
                if len(dynamic) == 2:
                    dynamic_score.append(
                        musiplectics.dynamic_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(dynamic[0]))
                    if dynamic[1] is not None:
                        dynamic_score.append(
                            musiplectics.dynamic_weights(
                                use_geometric_mean=use_geometric_mean,
                                use_total_playing_time=use_total_playing_time,
                                log_scale_values=log_scale_values).get(
                                    dynamic[1]))

                if use_product:
                    dynamics_complexity += reduce(mul, dynamic_score)
                else:
                    dynamics_complexity += reduce(add, dynamic_score)
                #dynamics_complexity += dynamic_score

                key_sig_score = musiplectics.key_sig_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get('KeySignature.' +
                                                           key_sig)
                key_sig_complexity += key_sig_score

                fret_position_score = musiplectics.fret_position_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(
                        fret_playing_postion)
                fret_playing_postion_complexity += fret_position_score

                # Playing postion shift is only the fretting hand.
                # If the note is played/fretted by the plucking hand
                # no shift should occur:
                if adorned_note.adornment.plucking.technique != 'tap':
                    shift_info = calculate_playing_shift(
                        adorned_note.note.fret_number, position_window)
                    position_window = shift_info[1]
                    shift_distance = shift_info[0]
                else:
                    shift_distance = 0

                if shift_distance >= 13:
                    shift_distance_score = musiplectics.shifting_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(str('13+'))
                else:
                    shift_distance_score = musiplectics.shifting_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            str(shift_distance))
                '''
                NOTE: Need to decide on what I should do with this!
                print shift_distance
                print "Exponetial shift: ", musiplectics.shifting_complexity_function(shift_distance, polynomial=False)
                print "Poly Shift: ", musiplectics.shifting_complexity_function(shift_distance)
                print 'Reg Shift: ', shift_distance_score
                '''

                shift_distance_complexity += shift_distance_score
                '''
                # Following the Musiplectics paper note complexity is the:
                # fret_position x technique x expression x articulation x
                #       dynamic x keysig x duration x timesig
                note_playing_complexity = (
                    fret_position_score * reduce(mul, playing_technique_note_scores) *
                    reduce(mul, expressive_techniques_score) * reduce(
                        mul, articulations_accent_score) * dynamic_score *
                    key_sig_score * duration_tempo_score * time_sig_score)
                '''

                # Adapting the Musiplectics original equation:
                # fret_position x technique x expression x articulation x
                #       dynamic x duration x timesig x bpm
                note_playing_complexity = (fret_position_score * reduce(
                    mul, playing_technique_note_scores) * reduce(
                        mul, expressive_techniques_score) * reduce(
                            mul, articulations_accent_score) * reduce(
                                mul, dynamic_score) * duration_tempo_score *
                                           time_sig_score * bpm_score)

                note_playing_complexities.append(note_playing_complexity)

                if unadorned_value:
                    note_playing_complexity_unadorned = (
                        fret_position_score * duration_tempo_score *
                        time_sig_score * bpm_score)
                    playing_technique_complexity_unadorned += 1
                    expressive_techniques_complexity_unadorned += 1
                    articulations_accents_complexity_unadorned += 1
                    dynamics_complexity_unadorned += 1
                    note_playing_complexities_unadorned.append(
                        note_playing_complexity_unadorned)

                # check the previous note:
                if previous_note is None:
                    previous_note = adorned_note
                else:
                    # sanity check that the previous note has finished
                    # before the adorned note starts:
                    if (previous_note.note.start_time +
                            previous_note.note.duration <=
                            adorned_note.note.start_time):
                        # calculate the complexity for the intervals, and
                        # techniques/things that occure between notes:
                        interval = calculate_pitch_interval(
                            adorned_note, previous_note)
                        interval_ioi = adorned_note.note.start_time - previous_note.note.start_time

                        # Get the interval complexity scores:
                        # add a restriction/limit to the interval so
                        # that it does not fall outside the complexity score range
                        if interval >= 21:
                            interval = 21

                        interval_score = musiplectics.interval_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(interval)
                        interval_complexity += interval_score

                        # Calculte the real time duration for the interval ioi
                        # and find the closest duration complexity for it:
                        interval_ioi_rt_duration = calculate_realtime_duration(
                            interval_ioi, bpm)
                        '''
                        duration_keys = sorted(
                            musiplectics.duration_scores().keys())
                        closest_interval_ioi_duration = calculate_closest_value()
                            duration_keys, interval_ioi_rt_duration)

                        interval_ioi_score = musiplectics.duration_scores(
                        ).get(closest_interval_ioi_duration)
                        '''

                        interval_ioi_score = musiplectics.duration_complexity_polynomial(
                            interval_ioi_rt_duration,
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values)
                        interval_ioi_complexity += interval_ioi_score

                        # work out if there is a change in dynamics:
                        dynamic_change = (
                            utilities.dynamics_inv.get(
                                adorned_note.note.dynamic.value) -
                            utilities.dynamics_inv.get(
                                previous_note.note.dynamic.value))

                        # default no dynamic change so it is the same
                        # as the adorned note

                        interval_dynamic = dynamic[0]

                        # if there is a change in dynamic, work out if
                        # it is a cressendo or diminuendo
                        if dynamic_change > 0:
                            # cressendo
                            interval_dynamic = 'cresc'

                        if dynamic_change < 0:
                            # diminuendo
                            interval_dynamic = 'dim'

                        interval_dynamic_score = musiplectics.dynamic_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(
                                interval_dynamic)

                        interval_dynamic_complexity += interval_dynamic_score

                        # interval expression is either none, or a slide
                        # as no other expression technique are used in the
                        # "playing" of an interval, and are instead confined
                        # modulating a single note
                        interval_expression = 'none'
                        if isinstance(
                                previous_note.adornment.fretting.modulation,
                                Slide):
                            interval_expression = 'slide'

                        interval_expression_score = musiplectics.expression_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(
                                interval_expression)
                        interval_expression_complexity += interval_expression_score

                        # work out the fret position of the interval:
                        # take the great fret postion and use that:
                        if adorned_note.note.fret_number >= previous_note.note.fret_number:
                            interval_fret_position = calculate_musiplectic_fret_possition(
                                adorned_note)
                        elif adorned_note.note.fret_number < previous_note.note.fret_number:
                            interval_fret_position = calculate_musiplectic_fret_possition(
                                previous_note)

                        interval_fret_position_score = musiplectics.fret_position_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(
                                interval_fret_position)
                        interval_fret_position_complexity += interval_fret_position_score
                        '''
                        # Following the Musiplectics paper interval complexity is the:
                        # interval x intervalIOI x dynamic x shifting distance x
                        #    fret position x any slide expression

                        interval_complexity = (
                            interval_score * interval_ioi_score *
                            interval_dynamic_score * shift_distance_score *
                            interval_fret_position_score * interval_expression_score)
                        note_interval_complexities.append(interval_complexity)
                        '''

                        # Adjusting the Musiplectics paper interval complexity:
                        # interval x intervalIOI x key_sig_score x dynamic x
                        #    shifting distance x fret position x any slide expression

                        interval_complexity = (
                            interval_score * interval_ioi_score * key_sig_score
                            * interval_dynamic_score * shift_distance_score *
                            interval_fret_position_score *
                            interval_expression_score)
                        note_interval_complexities.append(interval_complexity)
                        # update the previous note:
                        previous_note = adorned_note

                        if unadorned_value:
                            interval_dynamic_complexity_unadorned += 1
                            interval_expression_complexity_unadorned += 1
                            interval_complexity_unadorned = (
                                interval_score * interval_ioi_score *
                                key_sig_score * shift_distance_score *
                                interval_fret_position_score)
                            note_interval_complexities_unadorned.append(
                                interval_complexity_unadorned)

            # measure has changed:
            playing_complexity_vector = [
                playing_technique_complexity, duration_tempo_complexity,
                bpm_complexity, key_sig_complexity, time_sig_complexity,
                expressive_techniques_complexity,
                articulations_accents_complexity, dynamics_complexity,
                fret_playing_postion_complexity, interval_complexity,
                interval_ioi_complexity, shift_distance_complexity,
                interval_dynamic_complexity, interval_expression_complexity
            ]

            # musiplectics_playing_complexity = sum(note_playing_complexities) + sum(
            #    note_interval_complexities)

            musiplectics_playing_complexity = [
                sum(note_playing_complexities),
                sum(note_interval_complexities)
            ]

            if unadorned_value:
                playing_complexity_vector_unadorned = [
                    playing_technique_complexity_unadorned,
                    duration_tempo_complexity, bpm_complexity,
                    key_sig_complexity, time_sig_complexity,
                    expressive_techniques_complexity_unadorned,
                    articulations_accents_complexity_unadorned,
                    dynamics_complexity_unadorned,
                    fret_playing_postion_complexity, interval_complexity,
                    interval_ioi_complexity, shift_distance_complexity,
                    interval_dynamic_complexity_unadorned,
                    interval_expression_complexity_unadorned
                ]
                musiplectics_playing_complexity_unadorned = [
                    sum(note_playing_complexities_unadorned),
                    sum(note_interval_complexities_unadorned)
                ]

            # if calculating complexity by bar:
            if by_bar:
                # add 1 to bar count to reflect actual count
                # and not list indexing

                if raw_values:
                    if calculation_type == 'both' or calculation_type == 'Both':
                        complexity_by_bar[measure_number + 1] = Complexity(
                            musiplectics_playing_complexity,
                            playing_complexity_vector)
                        if unadorned_value:
                            complexity_by_bar_unadorned[
                                measure_number + 1] = Complexity(
                                    musiplectics_playing_complexity_unadorned,
                                    playing_complexity_vector_unadorned)

                    elif calculation_type == 'BGM' or calculation_type == 'bgm':
                        complexity_by_bar[measure_number + 1] = BGM(
                            musiplectics_playing_complexity)
                        if unadorned_value:
                            complexity_by_bar_unadorned[
                                measure_number + 1] = BGM(
                                    musiplectics_playing_complexity_unadorned)

                    elif calculation_type == 'EVC' or calculation_type == 'evc':
                        complexity_by_bar[measure_number +
                                          1] = EVC(playing_complexity_vector)
                        if unadorned_value:
                            complexity_by_bar_unadorned[
                                measure_number +
                                1] = EVC(playing_complexity_vector_unadorned)
                else:
                    if calculation_type == 'both' or calculation_type == 'Both':
                        complexity_by_bar[measure_number + 1] = Complexity(
                            sum(musiplectics_playing_complexity),
                            calculate_euclidean_complexity(
                                playing_complexity_vector))
                        if unadorned_value:
                            complexity_by_bar_unadorned[
                                measure_number + 1] = Complexity(
                                    sum(musiplectics_playing_complexity_unadorned
                                        ),
                                    calculate_euclidean_complexity(
                                        playing_complexity_vector_unadorned))

                    elif calculation_type == 'BGM' or calculation_type == 'bgm':
                        complexity_by_bar[measure_number + 1] = BGM(
                            sum(musiplectics_playing_complexity))
                        if unadorned_value:
                            complexity_by_bar_unadorned[
                                measure_number + 1] = BGM(
                                    sum(musiplectics_playing_complexity_unadorned
                                        ))

                    elif calculation_type == 'EVC' or calculation_type == 'evc':
                        complexity_by_bar[measure_number + 1] = EVC(
                            calculate_euclidean_complexity(
                                playing_complexity_vector))
                        if unadorned_value:
                            complexity_by_bar_unadorned[
                                measure_number + 1] = EVC(
                                    calculate_euclidean_complexity(
                                        playing_complexity_vector_unadorned))

                # reset the parameters:
                playing_technique_complexity = 0
                duration_tempo_complexity = 0
                key_sig_complexity = 0
                time_sig_complexity = 0
                bpm_complexity = 0
                expressive_techniques_complexity = 0
                articulations_accents_complexity = 0
                dynamics_complexity = 0
                fret_playing_postion_complexity = 0

                interval_complexity = 0
                interval_ioi_complexity = 0
                shift_distance_complexity = 0

                note_playing_complexities = []
                note_interval_complexities = []

                if unadorned_value:
                    playing_technique_complexity_unadorned = 0
                    expressive_techniques_complexity_unadorned = 0
                    articulations_accents_complexity_unadorned = 0
                    dynamics_complexity_unadorned = 0

                    interval_dynamic_complexity_unadorned = 0
                    interval_expression_complexity_unadorned = 0

                    note_interval_complexities_unadorned = []
                    note_playing_complexities_unadorned = []

                # parameters for interval calculations
                previous_note = None

        if by_bar:
            unadorned_complexity = None
            if unadorned_value:
                unadorned_complexity = complexity_by_bar_unadorned
                return output_complexities(complexity_by_bar,
                                           unadorned_complexity)
            else:
                return complexity_by_bar

        else:
            if raw_values:
                if calculation_type == 'both' or calculation_type == 'Both':
                    if unadorned_value:
                        return output_complexities(
                            Complexity(musiplectics_playing_complexity,
                                       playing_complexity_vector),
                            Complexity(
                                musiplectics_playing_complexity_unadorned,
                                playing_complexity_vector_unadorned))

                    else:
                        return Complexity(musiplectics_playing_complexity,
                                          playing_complexity_vector)
                elif calculation_type == 'BGM' or calculation_type == 'bgm':
                    if unadorned_value:
                        return output_complexities(
                            BGM(musiplectics_playing_complexity),
                            BGM(musiplectics_playing_complexity_unadorned))
                    else:
                        return BGM(musiplectics_playing_complexity)
                elif calculation_type == 'EVC' or calculation_type == 'evc':
                    if unadorned_value:
                        return output_complexities(
                            EVC(playing_complexity_vector),
                            EVC(playing_complexity_vector_unadorned))
                    else:
                        return EVC(playing_complexity_vector)
            else:
                if calculation_type == 'both' or calculation_type == 'Both':
                    if unadorned_value:
                        return output_complexities(
                            Complexity(
                                sum(musiplectics_playing_complexity),
                                calculate_euclidean_complexity(
                                    playing_complexity_vector)),
                            Complexity(
                                sum(musiplectics_playing_complexity_unadorned),
                                calculate_euclidean_complexity(
                                    playing_complexity_vector_unadorned)))
                    return Complexity(
                        sum(musiplectics_playing_complexity),
                        calculate_euclidean_complexity(
                            playing_complexity_vector))
                elif calculation_type == 'BGM' or calculation_type == 'bgm':
                    if unadorned_value:
                        return output_complexities(
                            BGM(sum(musiplectics_playing_complexity)),
                            BGM(
                                sum(musiplectics_playing_complexity_unadorned))
                        )
                    else:
                        return BGM(sum(musiplectics_playing_complexity))
                elif calculation_type == 'EVC' or calculation_type == 'evc':
                    if unadorned_value:
                        return output_complexities(
                            EVC(
                                calculate_euclidean_complexity(
                                    playing_complexity_vector)),
                            EVC(
                                calculate_euclidean_complexity(
                                    playing_complexity_vector_unadorned)))
                    return EVC(
                        calculate_euclidean_complexity(
                            playing_complexity_vector))

    if isinstance(input_data, Measure):

        measure = input_data
        # skip non-monophonic measures:
        if measure.meta_data.monophonic is False:
            '''
            if by_bar:
                # add 1 to bar count to reflect actual count
                # and not list indexing
                if calculation_type == 'both':
                    complexity_by_bar[measure_number + 1] = Complexity(None, None)
                elif calculation_type == 'BGM':
                    complexity_by_bar[measure_number + 1] = BGM(None)
                elif calculation_type == 'EVC':
                    complexity_by_bar[measure_number + 1] = EVC(None, None)
            '''

            return

        # measure info:
        key_sig = measure.meta_data.key_signature
        time_sig = measure.meta_data.time_signature

        # if the time sig doesn't have a complexity weight skip the measure
        if time_sig not in list(musiplectics.time_sig_weights().keys()):
            return

        bpm = measure.meta_data.tempo

        # work out tied note durations:
        measure_notes = calculate_tied_note_durations(measure)

        notelist = calculate_grace_note_possitions(measure_notes)

        for adorned_note in notelist:

            # Note info:
            playing_techniques = calculate_musiplectic_techniques(adorned_note)
            '''
                if adorned_note.note.duration == 0:
                    if adorned_note.note.notated_duration.value != 0:
                        rt_duration = calculate_realtime_duration(
                            adorned_note.note.notated_duration.value, bpm)
                else:
                '''

            rt_duration = calculate_realtime_duration(
                adorned_note.note.duration, bpm)
            #duration_tempo = calculate_musiplectics_duration(adorned_note, bpm)
            expressive_techniques = calculate_musiplectic_expression(
                adorned_note)
            articulations_accents = calculate_musiplectic_articulations(
                adorned_note)
            dynamic = calculate_musiplectic_dynamic(adorned_note)
            fret_playing_postion = calculate_musiplectic_fret_possition(
                adorned_note)

            # calculate the complexity values from note info:

            # variable to keep track of the complexity scores for techniques
            # in this note, used to calculate the full complexity score.
            playing_technique_note_scores = []

            for playing_technique in playing_techniques:
                # updated the playing technique complexity
                # playing_technique_complexity += musiplectics.technique_scores(
                # ).get(playing_technique)
                # and add the scores to the note score list
                playing_technique_note_scores.append(
                    musiplectics.technique_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            playing_technique))

            if use_product:
                playing_technique_complexity += reduce(
                    mul, playing_technique_note_scores)
            else:
                playing_technique_complexity += reduce(
                    add, playing_technique_note_scores)

            duration_tempo_score = musiplectics.duration_complexity_polynomial(
                rt_duration,
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values)
            duration_tempo_complexity += duration_tempo_score

            time_sig_score = musiplectics.time_sig_weights(
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values).get(time_sig)

            time_sig_complexity += time_sig_score

            bpm_list = sorted(
                musiplectics.tempo_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values)[0].keys())

            bpm_musiplectic = calculate_closest_value(bpm_list, bpm)

            bpm_score = musiplectics.tempo_weights(
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values)[0].get(
                    int(bpm_musiplectic))

            bpm_complexity += bpm_score

            expressive_techniques_score = []
            for expressive_technique in expressive_techniques:
                expressive_techniques_score.append(
                    musiplectics.expression_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            expressive_technique))

            if use_product:
                expressive_techniques_complexity += reduce(
                    mul, expressive_techniques_score)
            else:
                expressive_techniques_complexity += reduce(
                    add, expressive_techniques_score)

            articulations_accent_score = []

            if articulations_accents == []:
                # articulations_accents_complexity += musiplectics.articulation_scores().get(None)
                articulations_accent_score.append(
                    musiplectics.articulation_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(None))
            else:
                for articulations_accent in articulations_accents:
                    # articulations_accents_complexity += musiplectics.articulation_scores().get(articulations_accent)
                    articulations_accent_score.append(
                        musiplectics.articulation_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(
                                articulations_accent))

            if use_product:
                articulations_accents_complexity += reduce(
                    mul, articulations_accent_score)
            else:
                articulations_accents_complexity += reduce(
                    add, articulations_accent_score)

            dynamic_score = []
            if len(dynamic) == 2:
                dynamic_score.append(
                    musiplectics.dynamic_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(dynamic[0]))
                if dynamic[1] is not None:
                    dynamic_score.append(
                        musiplectics.dynamic_weights(
                            use_geometric_mean=use_geometric_mean,
                            use_total_playing_time=use_total_playing_time,
                            log_scale_values=log_scale_values).get(dynamic[1]))

            if use_product:
                dynamics_complexity += reduce(mul, dynamic_score)
            else:
                dynamics_complexity += reduce(add, dynamic_score)
            #dynamics_complexity += dynamic_score

            key_sig_score = musiplectics.key_sig_weights(
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values).get('KeySignature.' +
                                                       key_sig)
            key_sig_complexity += key_sig_score

            fret_position_score = musiplectics.fret_position_weights(
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values).get(fret_playing_postion)
            fret_playing_postion_complexity += fret_position_score

            # Playing postion shift is only the fretting hand.
            # If the note is played/fretted by the plucking hand
            # no shift should occur:
            if adorned_note.adornment.plucking.technique != 'tap':
                shift_info = calculate_playing_shift(
                    adorned_note.note.fret_number, position_window)
                position_window = shift_info[1]
                shift_distance = shift_info[0]
            else:
                shift_distance = 0

            if shift_distance >= 13:
                shift_distance_score = musiplectics.shifting_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(str('13+'))
            else:
                shift_distance_score = musiplectics.shifting_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(
                        str(shift_distance))
            '''
                NOTE: Need to decide on what I should do with this!
                print shift_distance
                print "Exponetial shift: ", musiplectics.shifting_complexity_function(shift_distance, polynomial=False)
                print "Poly Shift: ", musiplectics.shifting_complexity_function(shift_distance)
                print 'Reg Shift: ', shift_distance_score
                '''

            shift_distance_complexity += shift_distance_score
            '''
                # Following the Musiplectics paper note complexity is the:
                # fret_position x technique x expression x articulation x
                #       dynamic x keysig x duration x timesig
                note_playing_complexity = (
                    fret_position_score * reduce(mul, playing_technique_note_scores) *
                    reduce(mul, expressive_techniques_score) * reduce(
                        mul, articulations_accent_score) * dynamic_score *
                    key_sig_score * duration_tempo_score * time_sig_score)
                '''

            # Adapting the Musiplectics original equation:
            # fret_position x technique x expression x articulation x
            #       dynamic x duration x timesig x bpm
            note_playing_complexity = (fret_position_score * reduce(
                mul, playing_technique_note_scores) * reduce(
                    mul, expressive_techniques_score) * reduce(
                        mul, articulations_accent_score) * reduce(
                            mul, dynamic_score) * duration_tempo_score *
                                       time_sig_score * bpm_score)

            note_playing_complexities.append(note_playing_complexity)

            if unadorned_value:
                note_playing_complexity_unadorned = (
                    fret_position_score * duration_tempo_score * time_sig_score
                    * bpm_score)
                playing_technique_complexity_unadorned += 1
                expressive_techniques_complexity_unadorned += 1
                articulations_accents_complexity_unadorned += 1
                dynamics_complexity_unadorned += 1
                note_playing_complexities_unadorned.append(
                    note_playing_complexity_unadorned)

            # check the previous note:
            if previous_note is None:
                previous_note = adorned_note
            else:
                # sanity check that the previous note has finished
                # before the adorned note starts:
                if (previous_note.note.start_time + previous_note.note.duration
                        <= adorned_note.note.start_time):
                    # calculate the complexity for the intervals, and
                    # techniques/things that occure between notes:
                    interval = calculate_pitch_interval(
                        adorned_note, previous_note)
                    interval_ioi = adorned_note.note.start_time - previous_note.note.start_time

                    # Get the interval complexity scores:
                    # add a restriction/limit to the interval so
                    # that it does not fall outside the complexity score range
                    if interval >= 21:
                        interval = 21

                    interval_score = musiplectics.interval_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(interval)
                    interval_complexity += interval_score

                    # Calculte the real time duration for the interval ioi
                    # and find the closest duration complexity for it:
                    interval_ioi_rt_duration = calculate_realtime_duration(
                        interval_ioi, bpm)
                    '''
                        duration_keys = sorted(
                            musiplectics.duration_scores().keys())
                        closest_interval_ioi_duration = calculate_closest_value()
                            duration_keys, interval_ioi_rt_duration)

                        interval_ioi_score = musiplectics.duration_scores(
                        ).get(closest_interval_ioi_duration)
                        '''

                    interval_ioi_score = musiplectics.duration_complexity_polynomial(
                        interval_ioi_rt_duration,
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values)
                    interval_ioi_complexity += interval_ioi_score

                    # work out if there is a change in dynamics:
                    dynamic_change = (utilities.dynamics_inv.get(
                        adorned_note.note.dynamic.value) -
                                      utilities.dynamics_inv.get(
                                          previous_note.note.dynamic.value))

                    # default no dynamic change so it is the same
                    # as the adorned note

                    interval_dynamic = dynamic[0]

                    # if there is a change in dynamic, work out if
                    # it is a cressendo or diminuendo
                    if dynamic_change > 0:
                        # cressendo
                        interval_dynamic = 'cresc'

                    if dynamic_change < 0:
                        # diminuendo
                        interval_dynamic = 'dim'

                    interval_dynamic_score = musiplectics.dynamic_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            interval_dynamic)

                    interval_dynamic_complexity += interval_dynamic_score

                    # interval expression is either none, or a slide
                    # as no other expression technique are used in the
                    # "playing" of an interval, and are instead confined
                    # modulating a single note
                    interval_expression = 'none'
                    if isinstance(previous_note.adornment.fretting.modulation,
                                  Slide):
                        interval_expression = 'slide'

                    interval_expression_score = musiplectics.expression_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            interval_expression)
                    interval_expression_complexity += interval_expression_score

                    # work out the fret position of the interval:
                    # take the great fret postion and use that:
                    if adorned_note.note.fret_number >= previous_note.note.fret_number:
                        interval_fret_position = calculate_musiplectic_fret_possition(
                            adorned_note)
                    elif adorned_note.note.fret_number < previous_note.note.fret_number:
                        interval_fret_position = calculate_musiplectic_fret_possition(
                            previous_note)

                    interval_fret_position_score = musiplectics.fret_position_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            interval_fret_position)
                    interval_fret_position_complexity += interval_fret_position_score
                    '''
                        # Following the Musiplectics paper interval complexity is the:
                        # interval x intervalIOI x dynamic x shifting distance x
                        #    fret position x any slide expression

                        interval_complexity = (
                            interval_score * interval_ioi_score *
                            interval_dynamic_score * shift_distance_score *
                            interval_fret_position_score * interval_expression_score)
                        note_interval_complexities.append(interval_complexity)
                        '''

                    # Adjusting the Musiplectics paper interval complexity:
                    # interval x intervalIOI x key_sig_score x dynamic x
                    #    shifting distance x fret position x any slide expression

                    interval_complexity = (
                        interval_score * interval_ioi_score * key_sig_score *
                        interval_dynamic_score * shift_distance_score *
                        interval_fret_position_score *
                        interval_expression_score)
                    note_interval_complexities.append(interval_complexity)
                    # update the previous note:
                    previous_note = adorned_note

                    if unadorned_value:
                        interval_dynamic_complexity_unadorned += 1
                        interval_expression_complexity_unadorned += 1
                        interval_complexity_unadorned = (
                            interval_score * interval_ioi_score * key_sig_score
                            * shift_distance_score *
                            interval_fret_position_score)
                        note_interval_complexities_unadorned.append(
                            interval_complexity_unadorned)

        # measure has changed:
        playing_complexity_vector = [
            playing_technique_complexity, duration_tempo_complexity,
            bpm_complexity, key_sig_complexity, time_sig_complexity,
            expressive_techniques_complexity, articulations_accents_complexity,
            dynamics_complexity, fret_playing_postion_complexity,
            interval_complexity, interval_ioi_complexity,
            shift_distance_complexity, interval_dynamic_complexity,
            interval_expression_complexity
        ]

        # musiplectics_playing_complexity = sum(note_playing_complexities) + sum(
        #    note_interval_complexities)

        musiplectics_playing_complexity = [
            sum(note_playing_complexities),
            sum(note_interval_complexities)
        ]

        if unadorned_value:
            playing_complexity_vector_unadorned = [
                playing_technique_complexity_unadorned,
                duration_tempo_complexity, bpm_complexity, key_sig_complexity,
                time_sig_complexity,
                expressive_techniques_complexity_unadorned,
                articulations_accents_complexity_unadorned,
                dynamics_complexity_unadorned, fret_playing_postion_complexity,
                interval_complexity, interval_ioi_complexity,
                shift_distance_complexity,
                interval_dynamic_complexity_unadorned,
                interval_expression_complexity_unadorned
            ]
            musiplectics_playing_complexity_unadorned = [
                sum(note_playing_complexities_unadorned),
                sum(note_interval_complexities_unadorned)
            ]

        if raw_values:
            if calculation_type == 'both' or calculation_type == 'Both':
                if unadorned_value:
                    return output_complexities(
                        Complexity(musiplectics_playing_complexity,
                                   playing_complexity_vector),
                        Complexity(musiplectics_playing_complexity_unadorned,
                                   playing_complexity_vector_unadorned))

                else:
                    return Complexity(musiplectics_playing_complexity,
                                      playing_complexity_vector)
            elif calculation_type == 'BGM' or calculation_type == 'bgm':
                if unadorned_value:
                    return output_complexities(
                        BGM(musiplectics_playing_complexity),
                        BGM(musiplectics_playing_complexity_unadorned))
                else:
                    return BGM(musiplectics_playing_complexity)
            elif calculation_type == 'EVC' or calculation_type == 'evc':
                if unadorned_value:
                    return output_complexities(
                        EVC(playing_complexity_vector),
                        EVC(playing_complexity_vector_unadorned))
                else:
                    return EVC(playing_complexity_vector)
        else:
            if calculation_type == 'both' or calculation_type == 'Both':
                if unadorned_value:
                    return output_complexities(
                        Complexity(
                            sum(musiplectics_playing_complexity),
                            calculate_euclidean_complexity(
                                playing_complexity_vector)),
                        Complexity(
                            sum(musiplectics_playing_complexity_unadorned),
                            calculate_euclidean_complexity(
                                playing_complexity_vector_unadorned)))
                return Complexity(
                    sum(musiplectics_playing_complexity),
                    calculate_euclidean_complexity(playing_complexity_vector))
            elif calculation_type == 'BGM' or calculation_type == 'bgm':
                if unadorned_value:
                    return output_complexities(
                        BGM(sum(musiplectics_playing_complexity)),
                        BGM(sum(musiplectics_playing_complexity_unadorned)))
                else:
                    return BGM(sum(musiplectics_playing_complexity))
            elif calculation_type == 'EVC' or calculation_type == 'evc':
                if unadorned_value:
                    return output_complexities(
                        EVC(
                            calculate_euclidean_complexity(
                                playing_complexity_vector)),
                        EVC(
                            calculate_euclidean_complexity(
                                playing_complexity_vector_unadorned)))
                return EVC(
                    calculate_euclidean_complexity(playing_complexity_vector))


def calculate_playing_complexity_study(song,
                                       by_bar=True,
                                       monophonic_only=True,
                                       use_geometric_mean=True,
                                       use_total_playing_time=False,
                                       log_scale_values=True,
                                       use_product=True):
    '''
    This calculates the complexity of a song
    '''
    '''
    # Check for the weight set:
    if weight_set == 'GM':
        use_geometric_mean = True
        use_total_playing_time = False
        log_scale_values = False
    if weight_set == 'GMS':
        use_geometric_mean = True
        use_total_playing_time = False
        log_scale_values = True
    if weight_set == 'GMT':
        use_geometric_mean = True
        use_total_playing_time = True
        log_scale_values = False
    if weight_set == 'GMTS':
        use_geometric_mean = True
        use_total_playing_time = True
        log_scale_values = False
    if weight_set == 'RD':
        use_geometric_mean = False
        use_total_playing_time = False
        log_scale_values = False
    if weight_set == 'RDT':
        use_geometric_mean = False
        use_total_playing_time = True
        log_scale_values = False
    '''

    # pre_process the song data to remove rests
    # and to combine tied_notes together

    # calculate the triplet_feel note durations
    # calculate_triplet_feel_note_durations(song)

    # calculated the tied note_durations
    note_list = calculate_tied_note_durations(song)

    # Process the note list and insert the grace notes
    note_list = calculate_grace_note_possitions(note_list)

    measure_count = 0
    position_window = []

    playing_technique_complexity = 0
    duration_tempo_complexity = 0
    key_sig_complexity = 0
    time_sig_complexity = 0
    bpm_complexity = 0
    expressive_techniques_complexity = 0
    articulations_accents_complexity = 0
    dynamics_complexity = 0
    fret_playing_postion_complexity = 0

    interval_complexity = 0
    interval_ioi_complexity = 0
    shift_distance_complexity = 0
    interval_dynamic_complexity = 0
    interval_fret_position_complexity = 0
    interval_expression_complexity = 0

    note_playing_complexities = []
    note_interval_complexities = []

    complexity_by_bar = []

    # parameters for interval calculations
    previous_note = None

    interval_calc_notes = []

    for adorned_note in note_list:
        # Sometimes grace notes start in negative time
        # i.e. before the first beat of the song:
        if adorned_note.note.start_time >= 0:
            # if the note start_time is greater than or equal to 0
            # all is ok.
            # if not, then just treat things as using
            # measure 0 until notes have start_times greater
            # than or equal to zero

            # Use a while loop to increment the measure number
            while not calcuate_note_is_in_measure(
                    adorned_note, song.measures[measure_count]):

                # measure has changed:
                playing_complexity_vector = [
                    playing_technique_complexity, duration_tempo_complexity,
                    bpm_complexity, key_sig_complexity, time_sig_complexity,
                    expressive_techniques_complexity,
                    articulations_accents_complexity, dynamics_complexity,
                    fret_playing_postion_complexity, interval_complexity,
                    interval_ioi_complexity, shift_distance_complexity
                ]

                # musiplectics_playing_complexity = sum(note_playing_complexities) + sum(
                #    note_interval_complexities)

                musiplectics_playing_complexity = [
                    sum(note_playing_complexities),
                    sum(note_interval_complexities)
                ]

                # if calculating complexity by bar:
                if by_bar:
                    # add 1 to bar count to reflect actual count
                    # and not list indexing

                    complexity_by_bar.append([
                        measure_count + 1, musiplectics_playing_complexity,
                        playing_complexity_vector
                    ])
                    playing_technique_complexity = 0
                    duration_tempo_complexity = 0
                    key_sig_complexity = 0
                    time_sig_complexity = 0
                    bpm_complexity = 0
                    expressive_techniques_complexity = 0
                    articulations_accents_complexity = 0
                    dynamics_complexity = 0
                    fret_playing_postion_complexity = 0

                    interval_complexity = 0
                    interval_ioi_complexity = 0
                    shift_distance_complexity = 0

                    note_playing_complexities = []
                    note_interval_complexities = []

                    # parameters for interval calculations
                    previous_note = None

                # incease the measure count
                measure_count += 1

        # Check the measure is monophonic:
        if not song.measures[measure_count].meta_data.monophonic:
            print("Measure is not monophonic, no interval complexity can be calculated...")
            if monophonic_only:
                print("Skipping polyphonic measure....")
                measure_count += 1

        # then calculate the musiplectics score:

        # measure info:
        key_sig = song.measures[measure_count].meta_data.key_signature
        time_sig = song.measures[measure_count].meta_data.time_signature
        bpm = song.measures[measure_count].meta_data.tempo

        # Note info:
        playing_techniques = calculate_musiplectic_techniques(adorned_note)
        rt_duration = calculate_realtime_duration(adorned_note.note.duration,
                                                  bpm)
        #duration_tempo = calculate_musiplectics_duration(adorned_note, bpm)
        expressive_techniques = calculate_musiplectic_expression(adorned_note)
        articulations_accents = calculate_musiplectic_articulations(
            adorned_note)
        dynamic = calculate_musiplectic_dynamic(adorned_note)
        fret_playing_postion = calculate_musiplectic_fret_possition(
            adorned_note)

        # calculate the complexity values from note info:

        # variable to keep track of the complexity scores for techniques
        # in this note, used to calculate the full complexity score.
        playing_technique_note_scores = []

        for playing_technique in playing_techniques:
            # updated the playing technique complexity
            # playing_technique_complexity += musiplectics.technique_scores(
            # ).get(playing_technique)
            # and add the scores to the note score list
            playing_technique_note_scores.append(
                musiplectics.technique_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(playing_technique))

        if use_product:
            playing_technique_complexity += reduce(
                mul, playing_technique_note_scores)
        else:
            playing_technique_complexity += reduce(
                add, playing_technique_note_scores)

        duration_tempo_score = musiplectics.duration_complexity_polynomial(
            rt_duration,
            use_geometric_mean=use_geometric_mean,
            use_total_playing_time=use_total_playing_time,
            log_scale_values=log_scale_values)
        duration_tempo_complexity += duration_tempo_score

        time_sig_score = musiplectics.time_sig_weights(
            use_geometric_mean=use_geometric_mean,
            use_total_playing_time=use_total_playing_time,
            log_scale_values=log_scale_values).get(time_sig)
        time_sig_complexity += time_sig_score

        bpm_list = sorted(
            musiplectics.tempo_weights(
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values)[0].keys())

        bpm_musiplectic = calculate_closest_value(bpm_list, bpm)

        bpm_score = musiplectics.tempo_weights(
            use_geometric_mean=use_geometric_mean,
            use_total_playing_time=use_total_playing_time,
            log_scale_values=log_scale_values)[0].get(int(bpm_musiplectic))

        bpm_complexity += bpm_score

        expressive_techniques_score = []
        for expressive_technique in expressive_techniques:
            expressive_techniques_score.append(
                musiplectics.expression_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(
                        expressive_technique))

        if use_product:
            expressive_techniques_complexity += reduce(
                mul, expressive_techniques_score)
        else:
            expressive_techniques_complexity += reduce(
                add, expressive_techniques_score)

        articulations_accent_score = []

        if articulations_accents == []:
            # articulations_accents_complexity += musiplectics.articulation_scores().get(None)
            articulations_accent_score.append(
                musiplectics.articulation_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(None))
        else:
            for articulations_accent in articulations_accents:
                # articulations_accents_complexity += musiplectics.articulation_scores().get(articulations_accent)
                articulations_accent_score.append(
                    musiplectics.articulation_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            articulations_accent))

        if use_product:
            articulations_accents_complexity += reduce(
                mul, articulations_accent_score)
        else:
            articulations_accents_complexity += reduce(
                add, articulations_accent_score)

        dynamic_score = []
        if len(dynamic) == 2:
            dynamic_score.append(
                musiplectics.dynamic_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(dynamic[0]))
            if dynamic[1] is not None:
                dynamic_score.append(
                    musiplectics.dynamic_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(dynamic[1]))

        if use_product:
            dynamics_complexity += reduce(mul, dynamic_score)
        else:
            dynamics_complexity += reduce(add, dynamic_score)
        #dynamics_complexity += dynamic_score

        key_sig_score = musiplectics.key_sig_weights(
            use_geometric_mean=use_geometric_mean,
            use_total_playing_time=use_total_playing_time,
            log_scale_values=log_scale_values).get('KeySignature.' + key_sig)
        key_sig_complexity += key_sig_score

        fret_position_score = musiplectics.fret_position_weights(
            use_geometric_mean=use_geometric_mean,
            use_total_playing_time=use_total_playing_time,
            log_scale_values=log_scale_values).get(fret_playing_postion)
        fret_playing_postion_complexity += fret_position_score

        # Playing postion shift is only the fretting hand.
        # If the note is played/fretted by the plucking hand
        # no shift should occur:
        if adorned_note.adornment.plucking.technique != 'tap':
            shift_info = calculate_playing_shift(adorned_note.note.fret_number,
                                                 position_window)
            position_window = shift_info[1]
            shift_distance = shift_info[0]
        else:
            shift_distance = 0

        if shift_distance >= 13:
            shift_distance_score = musiplectics.shifting_weights(
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values).get(str('13+'))
        else:
            shift_distance_score = musiplectics.shifting_weights(
                use_geometric_mean=use_geometric_mean,
                use_total_playing_time=use_total_playing_time,
                log_scale_values=log_scale_values).get(str(shift_distance))
        '''
        NOTE: Need to decide on what I should do with this!
        print shift_distance
        print "Exponetial shift: ", musiplectics.shifting_complexity_function(shift_distance, polynomial=False)
        print "Poly Shift: ", musiplectics.shifting_complexity_function(shift_distance)
        print 'Reg Shift: ', shift_distance_score
        '''

        shift_distance_complexity += shift_distance_score
        '''
        # Following the Musiplectics paper note complexity is the:
        # fret_position x technique x expression x articulation x
        #       dynamic x keysig x duration x timesig
        note_playing_complexity = (
            fret_position_score * reduce(mul, playing_technique_note_scores) *
            reduce(mul, expressive_techniques_score) * reduce(
                mul, articulations_accent_score) * dynamic_score *
            key_sig_score * duration_tempo_score * time_sig_score)
        '''

        # Adapting the Musiplectics original equation:
        # fret_position x technique x expression x articulation x
        #       dynamic x duration x timesig x bpm
        note_playing_complexity = (
            fret_position_score * reduce(mul, playing_technique_note_scores) *
            reduce(mul, expressive_techniques_score) * reduce(
                mul, articulations_accent_score) * reduce(mul, dynamic_score) *
            duration_tempo_score * time_sig_score * bpm_score)

        note_playing_complexities.append(note_playing_complexity)

        # check the previous note:
        if previous_note is None:
            previous_note = adorned_note
        else:
            # sanity check that the previous note has finished
            # before the adorned note starts:
            if (previous_note.note.start_time + previous_note.note.duration <=
                    adorned_note.note.start_time):
                # calculate the complexity for the intervals, and
                # techniques/things that occure between notes:
                interval = calculate_pitch_interval(adorned_note,
                                                    previous_note)
                interval_ioi = adorned_note.note.start_time - previous_note.note.start_time

                # Get the interval complexity scores:
                # add a restriction/limit to the interval so
                # that it does not fall outside the complexity score range
                if interval >= 21:
                    interval = 21

                interval_score = musiplectics.interval_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(interval)
                interval_complexity += interval_score

                # Calculte the real time duration for the interval ioi
                # and find the closest duration complexity for it:
                interval_ioi_rt_duration = calculate_realtime_duration(
                    interval_ioi, bpm)
                '''
                duration_keys = sorted(
                    musiplectics.duration_scores().keys())
                closest_interval_ioi_duration = calculate_closest_value(
                    duration_keys, interval_ioi_rt_duration)

                interval_ioi_score = musiplectics.duration_scores(
                ).get(closest_interval_ioi_duration)
                '''

                interval_ioi_score = musiplectics.duration_complexity_polynomial(
                    interval_ioi_rt_duration,
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values)
                interval_ioi_complexity += interval_ioi_score

                # work out if there is a change in dynamics:
                dynamic_change = (
                    utilities.dynamics_inv.get(adorned_note.note.dynamic.value)
                    - utilities.dynamics_inv.get(
                        previous_note.note.dynamic.value))

                # default no dynamic change so it is the same
                # as the adorned note

                interval_dynamic = dynamic[0]

                # if there is a change in dynamic, work out if
                # it is a cressendo or diminuendo
                if dynamic_change > 0:
                    # cressendo
                    interval_dynamic = 'cresc'

                if dynamic_change < 0:
                    # diminuendo
                    interval_dynamic = 'dim'

                interval_dynamic_score = musiplectics.dynamic_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(interval_dynamic)

                interval_dynamic_complexity += interval_dynamic_score

                # interval expression is either none, or a slide
                # as no other expression technique are used in the
                # "playing" of an interval, and are instead confined
                # modulating a single note
                interval_expression = 'none'
                if isinstance(previous_note.adornment.fretting.modulation,
                              Slide):
                    interval_expression = 'slide'

                interval_expression_score = musiplectics.expression_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(interval_expression)
                interval_expression_complexity += interval_expression_score

                # work out the fret position of the interval:
                # take the great fret postion and use that:
                if adorned_note.note.fret_number >= previous_note.note.fret_number:
                    interval_fret_position = calculate_musiplectic_fret_possition(
                        adorned_note)
                elif adorned_note.note.fret_number < previous_note.note.fret_number:
                    interval_fret_position = calculate_musiplectic_fret_possition(
                        previous_note)

                interval_fret_position_score = musiplectics.fret_position_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(
                        interval_fret_position)
                interval_fret_position_complexity += interval_fret_position_score
                '''
                # Following the Musiplectics paper interval complexity is the:
                # interval x intervalIOI x dynamic x shifting distance x
                #    fret position x any slide expression

                interval_complexity = (
                    interval_score * interval_ioi_score *
                    interval_dynamic_score * shift_distance_score *
                    interval_fret_position_score * interval_expression_score)
                note_interval_complexities.append(interval_complexity)
                '''

                # Adjusting the Musiplectics paper interval complexity:
                # interval x intervalIOI x key_sig_score x dynamic x
                #    shifting distance x fret position x any slide expression

                interval_complexity = (
                    interval_score * interval_ioi_score * key_sig_score *
                    interval_dynamic_score * shift_distance_score *
                    interval_fret_position_score * interval_expression_score)
                note_interval_complexities.append(interval_complexity)
                # update the previous note:
                previous_note = adorned_note

    # Make a complexity vector to be used
    # in the playing complexity feature space:
    playing_complexity_vector = [
        playing_technique_complexity, duration_tempo_complexity, bpm_score,
        key_sig_complexity, time_sig_complexity,
        expressive_techniques_complexity, articulations_accents_complexity,
        dynamics_complexity, fret_playing_postion_complexity,
        interval_complexity, interval_ioi_complexity,
        shift_distance_complexity, interval_dynamic_complexity,
        interval_fret_position_complexity, interval_expression_complexity
    ]

    # musiplectics_playing_complexity = sum(note_playing_complexities) + sum(
    #    note_interval_complexities)

    musiplectics_playing_complexity = [
        sum(note_playing_complexities),
        sum(note_interval_complexities)
    ]

    if by_bar:
        # add 1 to bar count to reflect actual count
        # and not list indexing
        complexity_by_bar.append([
            measure_count + 1, musiplectics_playing_complexity,
            playing_complexity_vector
        ])
        return complexity_by_bar
    else:
        return musiplectics_playing_complexity, playing_complexity_vector


def calculate_euclidean_complexity(complexity_feature_list):
    '''
    Calculate the euclidean distance from the origin of the
    complexity feature space.
    '''
    euclidian_complexity = 0
    for value in complexity_feature_list:
        euclidian_complexity += pow(value, 2)

    return sqrt(euclidian_complexity)


def calculate_euclidean_distance_between_complexities(
        complexity_feature_list1, complexity_feature_list2):
    '''
    Calculate the distance between two complexity feature space vectors
    '''

    distance = 0
    for value1 in complexity_feature_list1:
        for value2 in complexity_feature_list2:
            distance += pow((value1 - value2), 2)

    return sqrt(distance)

    return


def calculate_peak_bar_complexity(complexity_by_bar_data,
                                  complexity_type='trad'):
    '''
    Calculate the complexity of each br in the complexity_by_bar_data
    return the bar with the highest values
    '''

    peak_bar = None
    for bar in complexity_by_bar_data:

        trad_musiplectic = sum(bar[1])
        note_musiplectic = bar[1][0]
        interval_musiplectic = bar[1][1]
        euclidean_musiplectic = calculate_euclidean_complexity(bar[2])

        if peak_bar is None:
            peak_bar = bar
        else:
            # if the musiplectics value of this bar
            # is greater than the peak bar, make this bar the peak_bar:
            if complexity_type == 'trad':
                if trad_musiplectic > sum(peak_bar[1]):
                    peak_bar = bar
            if complexity_type == 'trad-note':
                if note_musiplectic > peak_bar[1][0]:
                    peak_bar = bar
            if complexity_type == 'trad-interval':
                if interval_musiplectic > peak_bar[1][1]:
                    peak_bar = bar

            if complexity_type == 'euclid':
                if (euclidean_musiplectic > calculate_euclidean_complexity(
                        peak_bar[2])):
                    peak_bar = bar

    return peak_bar


###########################################
# Playing Feature Calculation Functions
###########################################


def calculate_adornment_to_note_ratio(input_data, technique):
    # Note: None are used

    total_notes = 0
    technique_count = 0

    if isinstance(input_data, Measure):
        for adorned_note in measure.notes:
            # read the technique:
            print()

    return technique_count / total_notes


def calculate_feature_type_count(musiplectics_features, feature_type_dict):
    '''

    '''

    if isinstance(musiplectics_features, list):
        for feature in musiplectics_features:
            if feature in feature_type_dict:
                # increment the feature count
                feature_type_dict[feature] += 1
            else:
                # add the feature to the feature_types dictionary
                # and give it a count of 1
                feature_type_dict[feature] = 1
    else:
        if musiplectics_features == 'none' or musiplectics_features == None:
            return feature_type_dict
        if musiplectics_features in feature_type_dict:
            # increment the feature count
            feature_type_dict[musiplectics_features] += 1
        else:
            # add the feature to the feature_types dictionary
            # and give it a count of 1
            feature_type_dict[musiplectics_features] = 1

    return feature_type_dict


def calculate_entropy(feature_dict, base=None):
    '''
    calculate's the entropy for a feature dictionary
    '''

    # first convert the count for each feature in
    # feature_dict into probabilities:
    feature_dict_probabilities = {}

    for key in list(feature_dict.keys()):
        feature_dict_probabilities[key + '_prob'] = (
            float(feature_dict.get(key)) / float(sum(feature_dict.values())))

    # calculate the entropy:
    entropy = 0

    for prob in list(feature_dict_probabilities.values()):
        base = 2 if base is None else base
        entropy -= prob * log(prob, base)

    return entropy


def calculate_features(song):
    '''

    '''

    # calculate the triplet_feel note durations
    calculate_triplet_feel_note_durations(song)
    note_list = calculate_tied_note_durations(song)

    position_window = []

    # Setup the Counters for each of adornment features.
    techniques = {}
    modifications = {}
    plucking_accents = {}
    fretting_accents = {}
    modulations = {}

    dynamics = {}
    fret_positions = {}

    durations = {}

    feature_type = {}

    for adorned_note in note_list:

        if adorned_note.adornment.fretting.technique is None:
            # no fretting technique overriding the plucking one
            techniques = calculate_feature_type_count(
                adorned_note.adornment.plucking.technique, techniques)
        else:
            # fretting technique overrides the plucking technique
            techniques = calculate_feature_type_count(
                adorned_note.adornment.fretting.technique, techniques)

        # work out the modification that could be applied:
        if adorned_note.adornment.plucking.modification is None:
            # No plucking modification applied but check
            # if a fretting is applied or not.
            # If it is override the techniques:
            if adorned_note.adornment.fretting.technique is None:
                modifications = calculate_feature_type_count(
                    adorned_note.adornment.fretting.modification,
                    modifications)
            else:
                modifications = calculate_feature_type_count(
                    'fretting', modifications)
        else:
            modifications = calculate_feature_type_count(
                adorned_note.adornment.plucking.modification, modifications)

        # get the plucking accent that is applied to the note:
        if adorned_note.adornment.plucking.accent is False:
            plucking_accents = calculate_feature_type_count(
                'no_accent', plucking_accents)
        elif adorned_note.adornment.plucking.accent is True:
            plucking_accents = calculate_feature_type_count(
                'accent', plucking_accents)

        # get the fretting accent that is applied to the note:
        if adorned_note.adornment.fretting.accent is False:
            fretting_accents = calculate_feature_type_count(
                'no_staccato', plucking_accents)
        elif adorned_note.adornment.fretting.accent is True:
            fretting_accents = calculate_feature_type_count(
                'staccato', plucking_accents)

        # get the fretting modulations applied to the note:
        if adorned_note.adornment.fretting.modulation is None:
            modulations = calculate_feature_type_count('no_modulation',
                                                       modulations)
        else:
            modulations = calculate_feature_type_count(
                calculate_musiplectic_expression(adorned_note), modulations)

        dynamics = calculate_feature_type_count(
            calculate_musiplectic_dynamic(adorned_note), dynamics)

        fret_postions = calculate_feature_type_count(
            calculate_musiplectic_fret_possition(adorned_note), fret_positions)

    # update all dicts into 1
    feature_type_dict = techniques.copy()
    feature_type_dict.update(modifications)
    feature_type_dict.update(plucking_accents)
    feature_type_dict.update(fretting_accents)
    feature_type_dict.update(modulations)
    feature_type_dict.update(dynamics)
    feature_type_dict.update(fret_postions)

    #print feature_type_dict

    # Here the rate and density for each adornement is calculated
    # and the entropy for each group of techniques applied to a note

    print(calculate_entropy(techniques))
    print(calculate_entropy(modifications))
    print(calculate_entropy(plucking_accents))
    print(calculate_entropy(fretting_accents))
    print(calculate_entropy(modulations))
    print(calculate_entropy(dynamics))
    print(calculate_entropy(fret_postions))

    # Calculate the rate: feature count / total_notes
    total_notes = len(note_list)

    total_duration = calculate_song_duration(song)

    features = {}
    for feature in list(feature_type_dict.keys()):

        # Calculate the rate: feature count / total_notes
        features[feature + '_rate'] = float(
            feature_type_dict[feature]) / float(total_notes)
        # Calculate the feature density: feature count / total_duration
        features[feature + '_density'] = float(
            feature_type_dict[feature]) / float(total_duration)

    print(features)
    return features


def calculate_feature_table(song):
    '''
    Calculate the features for the songs.

    Return a formatted table that can be merged with the SynPy
    and FANTASTIC features tables
    '''

    assert isinstance(song, Song), "must be a song input"

    # Features column numbers
    feature_col_numbers = {
        '2_finger_pluck': 1,
        'pick': 3,
        'slap': 5,
        'pop': 7,
        'tap': 9,
        'double_thumb': 11,
        'double_thumb_upstroke': 13,
        'double_thumb_downstroke': 15,
        'fretting_slap': 17,
        'hammer_on': 19,
        'pull_off': 21,
        'double_stop': 23,
        '3_note_chord': 25,
        '4_note_chord': 27,
        'natural_harmonic': 29,
        'artificial_harmonic': 21,
        'palm_mute': 23,
        'palm_mute_pluck': 25,
        'palm_mute_pick': 27,
        'palm_mute_thumb_pluck': 29,
        'dead_note': 31,
        'dead_note_pluck_pick': 33,
        'dead_note_slap': 35,
        'dead_note_pop': 37,
        'quater_bend': 39,
        'half_bend': 41,
        'whole_bend': 43,
        'vibrato': 45,
        'trill': 47,
        'slide': 49,
        '0-4': 51,
        '5-11': 53,
        '12-17': 55,
        '18+': 57,
        'staccato': 59,
        'accent': 61,
        'ppp': 63,
        'pp': 65,
        'p': 67,
        'mp': 69,
        'mf': 71,
        'f': 73,
        'ff': 75,
        'fff': 77,
    }

    csv_file = []
    csv_header = [
        'file.id', 'finger_rate', 'finger_density',
        'no_plucking_modification_rate', 'no_plucking_modification_density',
        '2_finger_pluck_rate', '2_finger_pluck_density', 'pick_rate',
        'pick_density', 'slap_rate', 'slap_density', 'pop_rate', 'pop_density',
        'tap_rate', 'tap_density', 'double_thumb_rate', 'double_thumb_density',
        'double_thumb_upstroke_rate', 'double_thumb_upstroke_density',
        'double_thumb_downstroke_rate', 'double_thumb_downstroke_density',
        'fretting_slap_rate', 'fretting_slap_density', 'hammer_on_rate',
        'hammer_on_density', 'pull_off_rate', 'pull_off_density',
        'double_stop_rate', 'double_stop_density', '3_note_chord_rate',
        '3_note_chord_density', '4_note_chord_rate', '4_note_chord_density',
        'natural_harmonic_rate', 'natural_harmonic_density',
        'artificial_harmonic_rate', 'artificial_harmonic_density',
        'palm_mute_rate', 'palm_mute_density', 'palm_mute_pluck_rate',
        'palm_mute_pluck_density', 'palm_mute_pick_rate',
        'palm_mute_pick_density', 'palm_mute_thumb_pluck_rate',
        'palm_mute_thumb_pluck_density', 'dead_note_rate', 'dead_note_density',
        'dead_note_pluck_pick_rate', 'dead_note_pluck_pick_density',
        'dead_note_slap_rate', 'dead_note_slap_density', 'dead_note_pop_rate',
        'dead_note_pop_density', 'quater_bend_rate', 'quater_bend_density',
        'half_bend_rate', 'half_bend_density', 'whole_bend_rate',
        'whole_bend_density', 'vibrato_rate', 'vibrato_density', 'trill_rate',
        'trill_density', 'slide_rate', 'slide_density', '0-4_rate',
        '0-4_density', '5-11_rate', '5-11_density', '12-17_rate',
        '12-17_density', '18+_rate', '18+_density', 'staccato_rate',
        'staccato_density', 'accent_rate', 'accent_density', 'ppp_rate',
        'ppp_density', 'pp_rate', 'pp_density', 'p_rate', 'p_density',
        'mp_rate', 'mp_density', 'mf_rate', 'mf_density', 'f_rate',
        'f_density', 'ff_rate', 'ff_density', 'fff_rate', 'fff_density'
    ]

    csv_file.append(csv_header)
    # file.id - this needs to match - song title.

    # make a default row with all values except the
    # file.id col set to 0
    default_row = []
    for col in csv_header:
        if col == 'file.id':
            default_row.append('')
        else:
            default_row.append(0)

    song_features = calculate_features(song)

    feature_row = default_row
    feature_row[csv_header.index('file.id')] = str(song.meta_data.title)
    for feature in list(song_features.keys()):
        feature_row[csv_header.index(feature)] = song_features.get(feature)
    csv_file.append(feature_row)

    return csv_file


def calculate_features_table_multiple_songs(rows):

    table_header = [
        'file.id', '2_finger_pluck_rate', '2_finger_pluck_density',
        'pick_rate', 'pick_density', 'slap_rate', 'slap_density', 'pop_rate',
        'pop_density', 'tap_rate', 'tap_density', 'double_thumb_rate',
        'double_thumb_density', 'double_thumb_upstroke_rate',
        'double_thumb_upstroke_density', 'double_thumb_downstroke_rate',
        'double_thumb_downstroke_density', 'fretting_slap_rate',
        'fretting_slap_density', 'hammer_on_rate', 'hammer_on_density',
        'pull_off_rate', 'pull_off_density', 'double_stop_rate',
        'double_stop_density', '3_note_chord_rate', '3_note_chord_density',
        '4_note_chord_rate', '4_note_chord_density', 'natural_harmonic_rate',
        'natural_harmonic_density', 'artificial_harmonic_rate',
        'artificial_harmonic_density', 'palm_mute_rate', 'palm_mute_density',
        'palm_mute_pluck_rate', 'palm_mute_pluck_density',
        'palm_mute_pick_rate', 'palm_mute_pick_density',
        'palm_mute_thumb_pluck_rate', 'palm_mute_thumb_pluck_density',
        'dead_note_rate', 'dead_note_density', 'dead_note_pluck_pick_rate',
        'dead_note_pluck_pick_density', 'dead_note_slap_rate',
        'dead_note_slap_density', 'dead_note_pop_rate',
        'dead_note_pop_density', 'quater_bend_rate', 'quater_bend_density',
        'half_bend_rate', 'half_bend_density', 'whole_bend_rate',
        'whole_bend_density', 'vibrato_rate', 'vibrato_density', 'trill_rate',
        'trill_density', 'slide_rate', 'slide_density', '0-4_rate',
        '0-4_density', '5-11_rate', '5-11_density', '12-17_rate',
        '12-17_density', '18+_rate', '18+_density', 'staccato_rate',
        'staccato_density', 'accent_rate', 'accent_density', 'ppp_rate',
        'ppp_density', 'pp_rate', 'pp_density', 'p_rate', 'p_density',
        'mp_rate', 'mp_density', 'mf_rate', 'mf_density', 'f_rate',
        'f_density', 'ff_rate', 'ff_density', 'fff_rate', 'fff_density'
    ]

    # Make the output file:
    table_out = []
    table_out.append(table_header)

    # append the row from *rows to to make the table
    for row in rows:
        for r in row:
            if r == table_header:
                continue
            table_out.append(r)

    return table_out


def calculate_physical_model_note_structures(
        input_data,
        matlab_engine=None,
        round_decimals=4,
        calculated_tied_notes=True,
        calculate_grace_notes=True):
    """Return a list of notes formated in the physical note structure


    Parameters
    ----------
    input_data : Song,
        This is the Song that is to be played by the physical model
    round_decimals : int, optional
        number of decimals to round the real-time values to (default = 4)

    Returns
    -------
    physical_model_notes : list of physical model notes
        A list of the notes to be played by the physical model

    """

    assert isinstance(input_data, Song), ("input_data must be a Song")
    
    if matlab_engine is None:
        matlab_engine = matlab.engine.start_matlab()

    # Add the physical model functions to matlab path
    p = matlab_engine.genpath('/Users/cg306/Documents/MATLAB')
    matlab_engine.addpath(p)

    song_duration = calculate_song_duration(input_data)

    note_list = []

    physical_model_notes = []

    cres_dim = False

    # calculated the tied note_durations and grace notes:
    if calculated_tied_notes:
        note_list = calculate_tied_note_durations(input_data)
    else:
        note_list = []
        for measure in input_data.measures:
            for note in measure.notes:
                note_list.append(note)

    if calculate_grace_notes:
        note_list = calculate_grace_note_possitions(note_list)
    # organise the note lists by measure
    # note_list_for_each_measure = calculate_bars_from_note_list(
    #    note_list, input_data)

    # Set tempo to first bar tempo:
    tempo = input_data.measures[0].meta_data.tempo

    adorned_note_index = 0

    for adorned_note in note_list:
        """
        for measure in input_data.measures:
            if calcuate_note_is_in_measure(adorned_note, measure):
                tempo = measure.meta_data.tempo
                break
        """

        previous_note = None
        next_note = None

        #print("adorned_note_index: ", adorned_note_index)

        if adorned_note_index > 0:
            previous_note = note_list[adorned_note_index - 1]

        if adorned_note_index + 1 < (len(note_list) - 1):
            next_note = note_list[adorned_note_index + 1]

        let_ring_dur_adjustment = 0
        no_out_slide = True
        # check if there is any outto slides:
        if adorned_note.adornment.fretting.modulation.slide is not None:
            if adorned_note.adornment.fretting.modulation.slide.outto is not None:
                no_out_slide = False

        if (adorned_note.adornment.fretting.modification.let_ring
                and no_out_slide):
            # Calculate let_ring duration:
            adorned_note_end = adorned_note.note.start_time + adorned_note.note.duration
            let_ring_dur_adjustment = (song_duration - adorned_note_end)
            # put the adorned_note in the shift window:
            shift, position_window = calculate_playing_shift(
                adorned_note.note.fret_number,
                position_window=[],
                position_window_size=4)
            for future_note in note_list[adorned_note_index:]:
                if future_note == adorned_note:
                    continue

                # put add the future note to the shift window:
                shift, position_window = calculate_playing_shift(
                    future_note.note.fret_number,
                    position_window=position_window,
                    position_window_size=4)

                if (future_note.note.string_number ==
                        adorned_note.note.string_number or shift > 0):
                    let_ring_dur_adjustment = (
                        future_note.note.start_time - adorned_note_end)
                    break

                if (future_note.adornment.fretting.modulation.slide is
                        not None):
                    if (future_note.adornment.fretting.modulation.slide.outto
                            == 'slide_shift'):
                        let_ring_dur_adjustment = (
                            future_note.note.start_time - adorned_note_end)
                        break

        # calculate cres./dim volume adjustments:
        if adorned_note.note.dynamic[1] is None:
            cres_dim = False
            cres_dim_increment = 0
            cres_dim_note_number = 0
        elif adorned_note.note.dynamic[1] is not None:

            if cres_dim is False:
                cres_dim_note_number = 1
                # calculate the parameters for the cres/dim:
                cres_dim = True
                cres_dim_starting_dynamic = adorned_note.note.dynamic[0]

                notes_in_cres_dim = 1

                for future_note in note_list[adorned_note_index:]:
                    if future_note == adorned_note:
                        continue

                    notes_in_cres_dim += 1

                    if future_note.note.dynamic[1] != adorned_note.note.dynamic[1]:
                        cres_dim_ending_dynamic = future_note.note.dynamic[0]
                        break

                dynamic_to_pm_dB = {
                    'fff': 0.0,
                    'ff': 2.2,
                    'f': 4.9,
                    'mf': 8.0,
                    'mp': 11.9,
                    'p': 16.9,
                    'pp': 23.9,
                    'ppp': 36.9
                }
                dynamic_dB_dif = (dynamic_to_pm_dB[cres_dim_starting_dynamic] -
                                  dynamic_to_pm_dB[cres_dim_ending_dynamic])

                if dynamic_dB_dif == 0:
                    if adorned_note.note.dynamic[1] == 'dim':
                        if cres_dim_starting_dynamic != 'ppp':
                            cres_dim_ending_dynamic = dynamic_to_pm_dB[
                                list(dynamic_to_pm_dB.keys()).index(
                                    cres_dim_starting_dynamic) + 1]

                    if adorned_note.note.dynamic[1] == 'cresc':
                        if cres_dim_starting_dynamic != 'fff':
                            cres_dim_ending_dynamic = dynamic_to_pm_dB[
                                list(dynamic_to_pm_dB.keys()).index(
                                    cres_dim_starting_dynamic) - 1]
                            dynamic_dB_dif = (
                                dynamic_to_pm_dB[cres_dim_starting_dynamic] -
                                cres_dim_ending_dynamic)

                cres_dim_increment = round(
                    float(dynamic_dB_dif / notes_in_cres_dim), round_decimals)
            if cres_dim:
                # already in a cres/dim
                cres_dim_note_number += 1

        (physical_model_note, string,
         py_m_note_struct) = calculate_physical_model_parameters(
             adorned_note,
             tempo,
             let_ring_dur_adjustment=let_ring_dur_adjustment,
             previous_note=previous_note,
             next_note=next_note,
             round_decimals=4,
             matlab_engine=matlab_engine)

        physical_model_note['dB'] = (
            physical_model_note['dB'] + cres_dim_increment)
        physical_model_notes.append({
            'note': physical_model_note,
            "string": string
        })

        adorned_note_index += 1

    # Check for grace notes that start before 0 and apply and offset
    # to all notes so that the timing starts from 0.
    if physical_model_notes[0]['note']['t_start'] < 0:
        offset = 0 - physical_model_notes[0]['note']['t_start']
        for pn_note in physical_model_notes:
            note_index = physical_model_notes.index(pn_note)
            physical_model_notes[note_index]['note']['t_start'] += offset
            physical_model_notes[note_index]['note']['t_end'] += offset

    # calculate the silence to append to complete the last bar:
    last_measure_end_time = (
        input_data.measures[-1].start_time + calculate_measure_duration(
            input_data.measures[-1]))
    last_note_end_time = calculate_note_endtime(note_list[-1])
    end_silence = last_measure_end_time - last_note_end_time

    end_silence_rt = round(
        calculate_realtime_duration(end_silence, tempo) / 1000, round_decimals)

    return physical_model_notes, end_silence_rt


def calculate_physical_model_pluck_style(adorned_note):

    physical_model_code = 'FS'

    if adorned_note.adornment.plucking.technique == 'finger':
        physical_model_code = 'FS'
        if adorned_note.adornment.plucking.modification.palm_mute:
            physical_model_code = 'MU'

    if (adorned_note.adornment.plucking.technique == 'pick'
            or adorned_note.adornment.plucking.technique == 'pick_up'
            or adorned_note.adornment.plucking.technique == 'pick_down'):
        physical_model_code = 'PK'

    if (adorned_note.adornment.plucking.technique == 'double_thumb'
            or adorned_note.adornment.plucking.technique ==
            'double_thumb_downstroke'
            or adorned_note.adornment.plucking.technique ==
            'double_thumb_upstroke'):
        physical_model_code = 'DT'

    if adorned_note.adornment.plucking.technique == 'pop':
        physical_model_code = 'SP'

    if adorned_note.adornment.plucking.technique == 'slap':
        physical_model_code = 'ST'

    if adorned_note.adornment.fretting.technique == 'tap':
        physical_model_code = 'TA'

    if adorned_note.adornment.fretting.technique == 'hammer-on':
        physical_model_code = 'HO'

    if adorned_note.adornment.fretting.technique == 'pull-off':
        physical_model_code = 'PO'

    return physical_model_code


def calculate_physical_model_parameters(adorned_note,
                                        tempo,
                                        let_ring_dur_adjustment=0,
                                        previous_note=None,
                                        next_note=None,
                                        slide_in_out_fret=5,
                                        trill_freq_max=7.0,
                                        round_decimals=4,
                                        matlab_engine=None):
    """Calculate the parameters to be passed into the CreateNotesStructure_callum


    """
    if matlab_engine is None:
        eng = matlab.engine.start_matlab()
        p = eng.genpath('/Users/cg306/Documents/MATLAB')
        eng.addpath(p)
    else:
        eng = matlab_engine

    let_ring_dur_adjustment = round(
        calculate_realtime_duration(let_ring_dur_adjustment, tempo) / 1000,
        round_decimals)

    fret_postions = eng.CalcFretPositions(100)[0]

    decay_rate = 3.0  # decay rate of note (dB/s)
    f_vib = 0.0
    cent = 0.0
    harm_str_fret = [0.0, 0.0, 0.0]
    slide_in_from = 0.0
    slide_out_to = 0.0

    # Set Pluck Style:
    pluck_style = calculate_physical_model_pluck_style(adorned_note)

    # Plucking Parameters:
    pluck_pos = round(15 + ((random.random() - random.random()) * 3),
                      round_decimals)
    summit_width = 4.0
    pick_pos = round(14 + ((random.random() - random.random())),
                     round_decimals)
    pick_strength = round(0.15 + ((random.random() - random.random()) * 0.1),
                          round_decimals)  # Value between 0 and 1
    damp_pluck_pos = round(10 - random.random() * 3, round_decimals)

    # Adjust slap position for double thumb technique:
    if pluck_style == 'DT':
        slap_pos = round(25 + ((random.random() - random.random())),
                         round_decimals)
    else:
        #33
        slap_pos = round(33 + ((random.random() - random.random())),
                         round_decimals)

    # If the previous note was a double thumb adjust the pop position:
    slap_pluck_pos = round(26 - random.random() * 1, round_decimals)
    if previous_note is not None:
        if calculate_physical_model_pluck_style(previous_note) == 'DT':
            slap_pluck_pos -= 8

    slap_width = 36.0

    physical_model_string = {1: 4.0, 2: 3.0, 3: 2.0, 4: 1.0, 5: 1.0}

    # pitch of the note:
    if adorned_note.note.fret_number < 20:

        #f0 = matlab_engine.Fret_Tone(
        #    'BA', physical_model_string[adorned_note.note.string_number],
        #    adorned_note.note.fret_number)

        f0 = round(utilities.midi2hz(adorned_note.note.pitch), 3)

        #print('f0: ' + str(f0))
        #print('Pitch: ' + str(round(utilities.midi2hz(adorned_note.note.pitch), 3)))
    else:
        f0 = round(utilities.midi2hz(adorned_note.note.pitch), 3)

    #if previous_note is not None:
    #    if previous_note.note.fret_number == 0 and pluck_style == 'HO':
    #        pluck_style = 'TA'

    # Set the stroke direction:
    stroke_direction = 'down'
    if (adorned_note.adornment.plucking.technique == 'pick_up'
            or adorned_note.adornment.plucking.technique ==
            'double_thumb_upstroke'):
        stroke_direction = 'up'

    if (adorned_note.adornment.plucking.technique == 'double_thumb_downstroke'
            or adorned_note.adornment.plucking.technique == 'pick_down'):
        stroke_direction = 'down'

    if (adorned_note.adornment.plucking.modification.palm_mute
            and pluck_style != "MU"):
        decay_rate = 25.0

        pluck_pos = damp_pluck_pos
        slap_pluck_pos = damp_pluck_pos
        if pluck_style == 'DT':
            slap_pluck_pos = 18
        else:
            slap_pos = damp_pluck_pos

    #if pluck_style == 'HO':
    #    if previous_note is not None:
    #        if previous_note.note.fret_number == 0:
    #            pluck_style == 'TA'
    #    else:

    if previous_note is None:

        # no previous now, so just set pull_off_from
        # to be this fret. Making the hammer-on a tap
        # ignored if not a hammer-on.
        pull_off_from = adorned_note.note.fret_number

        if pluck_style == 'PO':
            # pull_off needs to be set to be 2.0
            # so it is set to be above the note being fretted.
            pull_off_from = 2.0
    else:
        assert isinstance(previous_note, AdornedNote)
        pull_off_from = float(previous_note.note.fret_number -
                              adorned_note.note.fret_number)

    # Expression style:
    harm_pos = {
        1: 0,
        2: Fraction(1, 8),
        2.7: Fraction(1, 7),
        3: Fraction(1, 6),
        4: Fraction(1, 5),
        5: Fraction(1, 4),
        6: Fraction(2, 7),
        7: Fraction(1, 3),
        8: Fraction(3, 8),
        9: Fraction(2, 5),
        10: Fraction(3, 7),
        11: 0,
        12: Fraction(1, 2),
        13: 0,
        14: 0,
        15: Fraction(4, 7),
        16: Fraction(3, 5),
        17: Fraction(5, 8),
        18: 0,
        19: Fraction(2, 3),
        20: 0,
        21: 0,
        22: Fraction(5, 7),
        23: 0,
        24: Fraction(3, 4),
        #28: Fraction(4, 5),
        #: Fraction(5, 6),
        #: Fraction(6, 7)
    }

    expr_style = 'NO'
    if adorned_note.adornment.fretting.modification.type == 'dead-note':
        expr_style = 'DN'
    elif adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
        expr_style = 'HA'

        harm_str_fret = [
            float(physical_model_string[adorned_note.note.string_number]),
            float(harm_pos[adorned_note.note.fret_number]), 0.0
        ]
    elif isinstance(
            adorned_note.adornment.plucking.modification.artificial_harmonic,
            ArtificialHarmonic):
        # Also need to do some other adjustments....
        expr_style = 'HA'
        print("Artificial Harmonic settings:")
        # need to do a conversion to the harmonic format....
        equivalent_artificial_harmonic_fret = 0
        artificial_harmonic_octave = (adorned_note.adornment.plucking.
                                      modification.artificial_harmonic.octave)
        artificial_harmonic_pitch = (adorned_note.adornment.plucking.
                                     modification.artificial_harmonic.pitch)

        midinote = (
            adorned_note.note.fret_number +
            adorned_note.note.string_tuning[adorned_note.note.string_number])
        octave = calculate_artificial_harmonic_octave(
            artificial_harmonic_octave)

        interval = calculate_artificial_harmonic_interval(
            midinote, artificial_harmonic_pitch)

        # Conver the artificial harmonic [octave, interval] into
        # the equivelent natural harmonic fret:
        artificial_harmonic_to_equiv_fret = {
            [1, 0]: 12,
            [1, 8]: 7,
            [2, 0]: 5,
            [2, 4]: 9,
            [2, 8]: 3,
            [2, 10]: 2.7,
            [3, 0]: 2
        }

        equivalent_artificial_harmonic_fret = artificial_harmonic_to_equiv_fret(
            [octave, interval])

        harm_str_fret = [
            float(physical_model_string[adorned_note.note.string_number]),
            float(harm_pos[equivalent_artificial_harmonic_fret]),
            float(adorned_note.note.fret_number)
        ]

    if adorned_note.adornment.fretting.modulation.vibrato:
        expr_style = 'VI'
        cent = 25.0
        f_vib = 3.0

    bendpos = []
    bendval = []
    if adorned_note.adornment.fretting.modulation.bend is not None:
        expr_style = 'BE'

        bend = adorned_note.adornment.fretting.modulation.bend

        cent = float(bend.value)
        # Deal with the bend points:
        for BendPoint in bend.points:
            bendpos.append(BendPoint.position)
            # bendpoints2cents = 25
            bendval.append((BendPoint.value * 25))

    slide_in_from = adorned_note.note.fret_number
    slide_out_to = adorned_note.note.fret_number
    if adorned_note.adornment.fretting.modulation.slide is not None:
        expr_style = 'SL'
        # Need to deal with different slides...
        # this has the cent to slide to and the time...
        # so will need to possible check the next note depending
        # on the type of slide
        into = adorned_note.adornment.fretting.modulation.slide.into
        outto = adorned_note.adornment.fretting.modulation.slide.outto

        if next_note is not None:
            assert isinstance(next_note, AdornedNote)

        if outto == 'slide_legato' or outto == 'slide_shift':
            if next_note is not None:
                slide_out_to = next_note.note.fret_number

        if into == 'slide_from_below':
            if previous_note is not None:
                if previous_note.note.fret_number < adorned_note.note.fret_number:
                    fret_diff = (adorned_note.note.fret_number -
                                 previous_note.note.fret_number)
                    if fret_diff > 2:
                        slide_in_from = previous_note.note.fret_number + 2
                    elif fret_diff > 1:
                        slide_in_from = previous_note.note.fret_number + 1
                    else:
                        slide_in_from = previous_note.note.fret_number
                else:
                    if adorned_note.note.fret_number > 2:
                        slide_in_from = adorned_note.note.fret_number - 2
                    elif adorned_note.note.fret_number > 1:
                        slide_in_from = adorned_note.note.fret_number - 1
            else:
                if adorned_note.note.fret_number > slide_in_out_fret:
                    slide_in_from = adorned_note.note.fret_number - slide_in_out_fret
                else:
                    slide_in_from = 1

        if into == 'slide_from_above':
            if previous_note is not None:
                if previous_note.note.fret_number > adorned_note.note.fret_number:
                    fret_diff = (previous_note.note.fret_number -
                                 adorned_note.note.fret_number)
                    if fret_diff > 2:
                        slide_in_from = previous_note.note.fret_number - 2
                    elif fret_diff > 1:
                        slide_in_from = previous_note.note.fret_number - 1
                    else:
                        slide_in_from = previous_note.note.fret_number
                else:
                    slide_in_from = adorned_note.note.fret_number + 2
            else:
                slide_in_from = adorned_note.note.fret_number + slide_in_out_fret

        if outto == 'slide_out_below':
            if next_note is not None:
                if next_note.note.fret_number < adorned_note.note.fret_number:
                    slide_out_to = next_note.note.fret_number
                else:
                    if adorned_note.note.fret_number > 2:
                        slide_out_to = adorned_note.note.fret_number - 2
                    elif adorned_note.note.fret_number > 1:
                        slide_out_to = adorned_note.note.fret_number - 1

            elif adorned_note.note.fret_number > slide_in_out_fret:
                slide_out_to = adorned_note.note.fret_number - slide_in_out_fret
            else:
                slide_out_to = 1

        if outto == 'slide_out_above':
            if next_note is not None:
                if next_note.note.fret_number > adorned_note.note.fret_number:
                    slide_out_to = next_note.note.fret_number
                else:
                    slide_out_to = adorned_note.note.fret_number + 2
            else:
                slide_out_to = adorned_note.note.fret_number + slide_in_out_fret

    stacatto_factor = 1
    if adorned_note.adornment.fretting.accent:
        stacatto_factor = 0.5

    t_start = round(
        calculate_realtime_duration(adorned_note.note.start_time, tempo) /
        1000, round_decimals)
    t_end = round(
        calculate_realtime_duration(
            adorned_note.note.start_time +
            adorned_note.note.duration * stacatto_factor, tempo) / 1000,
        round_decimals)

    # trill depends on note durations:
    trill_freq = 0.0
    trill_fret = 0.0
    if adorned_note.adornment.fretting.modulation.trill is not None:
        expr_style = 'TR'

        trill = adorned_note.adornment.fretting.modulation.trill
        trill_fret = float(trill.fret - adorned_note.note.fret_number)

        if trill.notated_duration.value is None:
            trill_note_duration = Fraction(1, 64)

        else:
            trill_note_duration = trill.notated_duration.value  # duration of each trill note

        # need to work out how many notes:
        number_of_trill_notes = int(
            floor((adorned_note.note.duration * stacatto_factor) /
                  trill_note_duration))
        # Frequency of the trill:
        trill_freq = round(number_of_trill_notes / t_end, round_decimals)

        if trill_freq >= trill_freq_max:
            trill_freq = trill_freq_max

    # only have expressions for the lenght of the note:
    expr_time = t_end

    # adjust any let_ring durations now:
    t_end += let_ring_dur_adjustment

    # https://www.hedsound.com/p/midi-velocity-db-dynamics-db-and.html
    dynamic_to_pm_dB = {
        'fff': 0.0,
        'ff': 2.2,
        'f': 4.9,
        'mf': 8.0,
        'mp': 11.9,
        'p': 16.9,
        'pp': 23.9,
        'ppp': 36.9
    }

    accent_factor = 3
    dB_level_accent = {
        'fff': 0.0,
        'ff': 2.2 / accent_factor,
        'f': 2.7 / accent_factor,
        'mf': 3.1 / accent_factor,
        'mp': 3.9 / accent_factor,
        'p': 5 / accent_factor,
        'pp': 7 / accent_factor,
        'ppp': 21.6 / accent_factor
    }

    if adorned_note.adornment.plucking.accent:
        if adorned_note.adornment.ghost_note:
            dB = dynamic_to_pm_dB['ppp'] - dB_level_accent['ppp']
        else:
            dB = dynamic_to_pm_dB[adorned_note.note.
                                  dynamic[0]] - dB_level_accent[adorned_note.
                                                                note.dynamic[0]]

    else:
        if adorned_note.adornment.ghost_note:
            dB = dynamic_to_pm_dB['ppp']
        else:
            dB = dynamic_to_pm_dB[adorned_note.note.dynamic[0]]

    # convert the dB to negative and account for
    # the exponential mapping in the physical model
    if dB != 0:
        dB = round(-log(dB, 10), round_decimals)

    # Put all the parameters into a dict that is suitable for matlab:
    physical_model_note = calculate_physical_model_parameter_dict(
        f0, pluck_style, stroke_direction, expr_style, cent, f_vib,
        harm_str_fret, t_start, t_end, dB, decay_rate, bendpos, bendval,
        slide_in_from, slide_out_to, pluck_pos, summit_width, pick_pos,
        pick_strength, damp_pluck_pos, slap_pos, slap_pluck_pos, slap_width,
        pull_off_from, trill_freq, trill_fret, expr_time,
        adorned_note.adornment.plucking.accent)
    py_m_note_struct = matlab_engine.CreateNotesStructure_callum(
        f0, pluck_style, stroke_direction, expr_style, cent, f_vib,
        harm_str_fret, t_start, t_end, dB, decay_rate, matlab.double(bendpos),
        matlab.double(bendval), slide_in_from, slide_out_to, pluck_pos,
        summit_width, pick_pos, pick_strength, damp_pluck_pos, slap_pos,
        slap_pluck_pos, slap_width, pull_off_from, trill_freq, trill_fret,
        expr_time, adorned_note.adornment.plucking.accent)
    return physical_model_note, physical_model_string[
        adorned_note.note.string_number], py_m_note_struct


def calculate_physical_model_parameter_dict(
        f0, pluck_style, stroke_direction, expr_style, cent, f_vib,
        harm_str_fret, t_start, t_end, dB, decay_rate, bendpos, bendval,
        slide_in_from, slide_out_to, pluck_pos, summit_width, pick_pos,
        pick_strength, damp_pluck_pos, slap_pos, slap_pluck_pos, slap_width,
        pull_off_from, trill_freq, trill_fret, expr_time, accent):
    physical_model_note = {}
    physical_model_note['f0'] = f0
    physical_model_note['dB'] = dB
    physical_model_note['decay_rate'] = decay_rate
    physical_model_note['t_start'] = t_start
    physical_model_note['t_end'] = t_end
    physical_model_note['pluck_style'] = pluck_style
    physical_model_note['expr_style'] = expr_style
    physical_model_note['stroke_direction'] = stroke_direction
    physical_model_note['f_vib'] = f_vib
    physical_model_note['cent'] = cent
    physical_model_note['harm_str_fret'] = matlab.double(harm_str_fret)
    physical_model_note['slide_in_from'] = slide_in_from
    physical_model_note['slide_out_to'] = slide_out_to
    physical_model_note['bendpos'] = matlab.double(bendpos)
    physical_model_note['bendval'] = matlab.double(bendval)
    physical_model_note['pluck_pos'] = pluck_pos
    physical_model_note['summit_width'] = summit_width
    physical_model_note['pick_pos'] = pick_pos
    physical_model_note['pick_strength'] = pick_strength
    physical_model_note['damp_pluck_pos'] = damp_pluck_pos
    physical_model_note['slap_pos'] = slap_pos
    physical_model_note['slap_pluck_pos'] = slap_pluck_pos
    physical_model_note['slap_width'] = slap_width
    physical_model_note['pull_off_from'] = pull_off_from
    physical_model_note['trill_freq'] = trill_freq
    physical_model_note['trill_fret'] = trill_fret
    physical_model_note['expr_time'] = expr_time
    physical_model_note['accent'] = accent

    return physical_model_note


def calculate_heuristic(complexity1,
                        complexity2,
                        difficulty1,
                        difficulty2,
                        complexity_weight=1,
                        difficulty_weight=1):
    """Return the result of the hueristic comparison calculation:

    """
    return ((complexity1 - complexity2) * complexity_weight +
            (difficulty1 - difficulty2) * difficulty_weight)


def calculate_FANTASTIC_features_for_note_pair(note1, note2, measure):
    """

    """

    assert isinstance(note1, AdornedNote) or isinstance(note1, Note)
    assert isinstance(note2, AdornedNote) or isinstance(note2, Note)

    bpm = measure.meta_data.tempo

    if isinstance(note1, AdornedNote):
        p1 = note1.note.pitch
        d1 = note1.note.duration
        if d1 == 0 and note1.note.notated_duration.value != 0:
            d1 = note1.note.notated_duration.value
        s1 = note1.note.start_time
    if isinstance(note1, Note):
        p1 = note1.pitch
        d1 = note1.duration
        if d1 == 0 and note1.notated_duration.value != 0:
            d1 = note1.notated_duration.value
        s1 = note1.start_time
    if isinstance(note2, AdornedNote):
        p2 = note2.note.pitch
        d2 = note2.note.duration
        if d2 == 0 and note2.note.notated_duration.value != 0:
            d2 = note2.note.notated_duration.value
        s2 = note2.note.start_time
    if isinstance(note2, Note):
        p2 = note2.pitch
        d2 = note2.note.duration
        if d2 == 0 and note2.notated_duration.value != 0:
            d2 = note2.notated_duration.value
        s2 = note2.start_time

    p = [p1, p2]
    p_range = max(p) - min(p)
    p_mean = sum(p) / len(p)

    p_std = sqrt(pow(p1 - p_mean, 2) + pow(p2 - p_mean, 2))

    #p_entropy
    if p1 != p2:
        fi = 0.5
    if p1 == p2:
        fi = 1

    p_entropy = -((fi * log(fi, 2) + fi * log(fi, 2)) / log(2, 2))

    # pitch intervals:
    interval = p2 - p1
    i_mode = interval
    i_abs_mean = abs(interval)
    i_abs_std = 0
    i_entropy = 0

    # duration:
    delta_t = [
        calculate_realtime_duration(d1, bpm) / 1000,
        calculate_realtime_duration(d2, bpm) / 1000
    ]

    #tatums = smallest unit in the measure
    delta_T = [d1, d2]
    tantum = min(delta_T)

    #print(measure)
    #print(delta_T)

    delta_T = [d1 / tantum, d2 / tantum]

    d_range = max(delta_t) - min(delta_t)
    d_median = sum(delta_T) / 2
    d_mode = max(delta_T)
    #d_entropy
    if d1 != d2:
        fi = 0.5
    if d1 == d2:
        fi = 1
    d_entropy = -((fi * log(fi, 2) + fi * log(fi, 2)) / log(2, 2))

    length = 2
    glob_duration = calculate_realtime_duration(
        s2, bpm) / 1000 - calculate_realtime_duration(s1, bpm) / 1000

    note_dens = length / glob_duration

    return {
        "p.range": p_range,
        "p.mean": p_mean,
        "p.std": p_std,
        "p.entropy": p_entropy,
        "i.abs.mean": i_abs_mean,
        "i.abs.std": i_abs_std,
        "i.mode": i_mode,
        "i.entropy": i_entropy,
        "d.range": d_range,
        "d.median": float(d_median),
        "d.mode": float(d_mode),
        "d.entropy": d_entropy,
        "len": length,
        "glob.duration": glob_duration,
        "note.dens": note_dens
    }


if __name__ == "__main__":
    print("hello")
