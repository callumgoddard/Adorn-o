

import os
from fractions import Fraction
from math import sqrt
from operator import mul
import csv

from rpy2.robjects import r
from collections import namedtuple
import guitarpro

# Possibly need these for matching CHARM things....
#from backports.pampy import match, HEAD, TAIL, _
# import difflib

import parser.API.calculate_functions as calculate
from parser.API.read_functions import read_basic_note_data
from parser.API.datatypes import *
import parser.API.update_functions as update
import parser.utilities as utilities
import feature_analysis as feature_analysis
from evaluation import musiplectics
import cbr
from functools import reduce

SelectedAdornedMeasure = namedtuple("SelectedAdornedMeasure",
                                    ['measure', 'complexity'])


def reuse(unadorned_measure,
          unadorned_measure_notes,
          adorned_measures,
          complexity_weight,
          difficulty_weight,
          weight_set='RD',
          gp5_wellformedness=True):
    """ Apply the adornments from the adorned measure
    to the unadorned measure

    Parameters
    ---------
    unadorned_measure, adorned_measures : Measure
        These are measures, the adornements from adorned_measure
        will be applied to the unadorned_measure.

    complexity_weight, difficulty_weight : -1 to 1
        Sets the weighting for the complexity and difficulty values
        for the newly_adorned_note selection criteria.
        0 means the value is ignored
        +ve numbers mean the value is maximised.
        -ve the value is minimised.

    gp5_wellformedness : boolean
        Set True to restrict the adornments to be wellformed for gp5
        file format. Set False to allow for any possible combination
        following the bass playing ontology.

    Returns
    ------
    new_adorned_measure : SelectedAdornedMeasure
        This is the unadornmed_measure with the adornments
        applied from the adorned_measure

    """

    # if the adorned_measure is a measure make it a list:
    if isinstance(adorned_measures, Measure):
        adorned_measures = [adorned_measures]

    new_adorned_measures = reuse_measures(
        unadorned_measure=unadorned_measure,
        unadorned_measure_notes=unadorned_measure_notes,
        adorned_measures=adorned_measures,
        complexity_weight=complexity_weight,
        difficulty_weight=difficulty_weight,
        weight_set=weight_set,
        chunk_size=3)

    #print("possible measures:", len(new_adorned_measures))

    print("selecting_measure...")
    selected_newly_adorned_measure = None
    for measure in new_adorned_measures:

        assert len(measure.notes) == len(unadorned_measure_notes)

        if selected_newly_adorned_measure is None:
            measure_complexities = calculate.calculate_playing_complexity(
                measure, song=None, by_bar=False, weight_set=weight_set)

            selected_newly_adorned_measure = SelectedAdornedMeasure(
                measure, measure_complexities)
        else:
            #print('comparing heuristics...')

            # Calculate the complexites for the measure:
            measure_complexities = calculate.calculate_playing_complexity(
                measure, song=None, by_bar=False, weight_set=weight_set)

            #print(measure_complexities)

            assert measure_complexities is not None, "No measure complexities calculated"

            # compare and pick the best measure:
            if calculate.calculate_heuristic(
                    measure_complexities.BGM,
                    selected_newly_adorned_measure.complexity.BGM,
                    measure_complexities.EVC,
                    selected_newly_adorned_measure.complexity.EVC,
                    complexity_weight, difficulty_weight) >= 0:
                # if ((measure_complexities.BGM - selected_newly_adorned_measure.
                #     complexity.BGM) * complexity_weight +
                #    (measure_complexities.EVC - selected_newly_adorned_measure.
                #     complexity.EVC) * difficulty_weight) >= 0:

                selected_newly_adorned_measure = SelectedAdornedMeasure(
                    measure, measure_complexities)
        """
        for row in data[1:]:
                sorted_index = 0
                for sorted_row in sorted_data:
                    heuristic = calculate_heuristic(
                        float(row[self.header.index(complexity_header)]),
                        float(sorted_row[self.header.index(complexity_header)]),
                        float(row[self.header.index(difficulty_header)]),
                        float(sorted_row[self.header.index(difficulty_header)]),
                        complexity_weight, difficulty_weight)
                    if heuristic >= 0:
                        break
                    sorted_index += 1
                sorted_data.insert(sorted_index, row)
        """

    # Clear new_adorned_measures
    del new_adorned_measures

    for note in selected_newly_adorned_measure.measure.notes:
        if isinstance(note, AdornedNote):
            assert isinstance(note.adornment.ghost_note, bool)

    return selected_newly_adorned_measure


def select_measure(measures, complexity_weight=1, difficulty_weight=1):

    return


def reuse_measures(unadorned_measure,
                   unadorned_measure_notes,
                   adorned_measures,
                   complexity_weight,
                   difficulty_weight,
                   weight_set,
                   chunk_size=3,
                   gp5_wellformedness=True):

    new_measures = []

    for adorned_measure in adorned_measures:

        chunks = match_up_unadorned_measure_chunks_with_adorned_measure_chunks(
            unadorned_measure=unadorned_measure,
            unadorned_measure_notes=unadorned_measure_notes,
            adorned_measure=adorned_measure,
            chunk_size=chunk_size)

        assert len(chunks) == 2

        matches = consolidate_note_sequnces_matches_to_note_matches(
            chunks[0], chunks[1])

        best_note_newly_adorned_notes = []
        for matched in matches:

            #print(matched.unadorned_note)
            #print(len(matched.adorned_notes))
            print(unadorned_measure.meta_data.number)
            print(matched.unadorned_note.note.note_number)

            adornments = find_all_possible_adornements(
                matched.unadorned_note, matched.adorned_notes,
                unadorned_measure, adorned_measure)

            pos_adornments = make_all_possible_adornments(
                adornments.plucking_accents, adornments.fretting_accents,
                adornments.plucking_techniques,
                adornments.plucking_modifications_ah,
                adornments.plucking_modifications_palm_mute,
                adornments.fretting_techniques,
                adornments.fretting_modifications_type,
                adornments.fretting_modifications_let_ring,
                adornments.fretting_modulations_bend,
                adornments.fretting_modulations_trill,
                adornments.fretting_modulations_vib,
                adornments.fretting_modulations_slide, adornments.grace_notes,
                adornments.ghost_notes, complexity_weight, difficulty_weight,
                gp5_wellformedness)

            best_note = select_best_adornment_for_unadorned_note(
                matched.unadorned_note, pos_adornments, adornments.dynamics,
                unadorned_measure, complexity_weight, difficulty_weight,
                weight_set)

            best_note_newly_adorned_notes.append(best_note)

            # Delete the adornments:
            del adornments, best_note

        #assert len(best_note_newly_adorned_notes) == len(
        #    calculate.calculate_tied_note_durations(unadorned_measure))

        assert  len(best_note_newly_adorned_notes) == len(unadorned_measure_notes)

        # put the best newly adorned notes back in the measure:
        new_measure = Measure(
            meta_data=unadorned_measure.meta_data,
            start_time=unadorned_measure.start_time,
            notes=best_note_newly_adorned_notes)

        # revise the measure:
        new_measure = cbr.revise(
            new_measure, revise_for_gp5=gp5_wellformedness)

        if new_measure not in new_measures:
            new_measures.append(new_measure)

        del new_measure, best_note_newly_adorned_notes, matches, chunks

    return new_measures


'''""
def reuse_old(unadorned_measure, adorned_measure):
    """ Apply the adornments from the adorned measure
    to the unadorned measure

    Parameters
    ---------
    unadorned_measure, adorned_measure : Measure
        These are measures, the adornements from adorned_measure
        will be applied to the unadorned_measure.

    Returns
    ------
    new_adorned_measure : Measure
        This is the unadornmed_measure with the adornments
        applied from the adorned_measure

    """

    assert isinstance(unadorned_measure,
                      Measure), ("unadorned_measure is not of type Measure")
    assert isinstance(adorned_measure,
                      Measure), ("adorned_measure is not of type Measure")

    # get the adorned note start_times:
    # relative to the start of the bar:
    adorned_note_start_times = []
    for adorned_note in adorned_measure.notes:
        adorned_note_start_times.append(adorned_note.note.start_time -
                                        adorned_measure.start_time)

    print(adorned_note_start_times)

    for unadorned_note in unadorned_measure.notes:

        # see if there is an adorned_note with the same start_time
        if (unadorned_note.note.start_time -
                unadorned_measure.start_time) in adorned_note_start_times:
            print("same start_time")

            # get the adorned note....
            adorned_note = adorned_measure.notes[
                adorned_note_start_times.index(unadorned_note.note.start_time)]

        else:

            # find the closest notes of the adorned measure
            closest_note_start = (calculate.calculate_closest_value(
                adorned_note_start_times,
                unadorned_note.note.start_time - unadorned_measure.start_time,
                'closest'))
            adorned_note_index = adorned_note_start_times.index(
                closest_note_start)

            # note to transfer adornements from:
            adorned_note = adorned_measure.notes[adorned_note_index]

        # then adorn the unadorned note with the adornments
        # from the adorned note.

        # not sure is duration is an issue.....
        # then see if the duration is the same:
        #if unadorned_note.note.duration == adorned_note.note.duration:

        if unadorned_note.note.pitch == adorned_note.note.pitch:
            # then see if the pitch is the same:
            if (unadorned_measure.meta_data.key_signature ==
                    adorned_measure.meta_data.key_signature
                    or relative_minor.get(
                        unadorned_measure.meta_data.key_signature) ==
                    adorned_measure.meta_data.key_signature
                    or unadorned_measure.meta_data.key_signature ==
                    relative_minor.get(
                        adorned_measure.meta_data.key_signature)):
                # also the same key sigs...
                # then they basically are the same note:
                # apply the adornments from the adorned_note
                # directly to the unadorned note:
                unadorned_note = (apply_adornments_from_adorned_note(
                    unadorned_note, adorned_note, "directly"))
            else:
                # different key sigs....
                unadorned_note = (apply_adornments_from_adorned_note(
                    unadorned_note, adorned_note, "key_change"))
        else:
            # different pitch....
            if (unadorned_measure.meta_data.key_signature ==
                    adorned_measure.meta_data.key_signature
                    or relative_minor.get(
                        unadorned_measure.meta_data.key_signature) ==
                    adorned_measure.meta_data.key_signature
                    or unadorned_measure.meta_data.key_signature ==
                    relative_minor.get(
                        adorned_measure.meta_data.key_signature)):
                # but same key sig:
                unadorned_note = (apply_adornments_from_adorned_note(
                    unadorned_note, adorned_note, "pitch_change"))
            else:
                # and different key_sig....
                unadorned_note = (apply_adornments_from_adorned_note(
                    unadorned_note, adorned_note, "key_and_pitch_change"))
    return


def apply_adornments_from_adorned_note(unadorned_note, adorned_note, method):
    """Adorn the unadorned note with adornements from the adorned note

    Parameters
    ----------
    unadorned_note, adorned_note : AdornedNote
        notes of type AdornedNote, the adornements for the adorned_note
        will be applied to the unadorned_note

    method : {"direct"}

    Returns
    -------
    newly_adorned_note : AdornedNote
        This is the unadorned_note with the adornemnets applied
        from the adorned_note

    False
        Returned if the adornments could not be applied to the
        unadorned note.

    """
    methods = ["direct", "key_change", "pitch_change", "key_and_pitch_change"]

    assert isinstance(unadorned_note,
                      AdornedNote), ("unadorned_note is not type AdornedNote")
    assert isinstance(adorned_note,
                      AdornedNote), ("adorned_note is not type AdornedNote")
    assert method in methods, (
        "Not reccognised method, must be one of: %s" % methods)

    if method == "direct":
        print("Applying adornments from adorned_note directly....")
        newly_adorned_note = update.update_adorned_note(
            unadorned_note, adornment=adorned_note.adornment)
        newly_adorned_note = update.update_note_in_adorned_note(
            newly_adorned_note, dynamic=adorned_note.note.dynamic)
        return newly_adorned_note

    return False
'''

relative_minor = {
    "CMajor": "AMinor",
    "FMajor": "DMinor",
    "BMajorFlat": "GMinor",
    "EMajorFlat": "CMinor",
    "AMajorFlat": "FMinor",
    "DMajorFlat": "BMinorFlat",
    "GMajorFlat": "EMinorFlat",
    "CMajorFlat": "AMinorFlat",
    "GMajor": "EMinor",
    "AMajor": "FMinorSharp",
    "EMajor": "CMinorSharp",
    "BMajor": "GMinorSharp",
    "FMajorSharp": "DMinorSharp",
    "CMajorSharp": "AMinorSharp",
}


def resue_dynamic_adornments(unadorned_measure, adorned_measure):
    """Find the appropriate places to reuse the dynamics from
    the adorned measure and adorn the unadorned measure with the.

    Parameters
    ----------
    unadorned_measure, adorned_measure : Measure
        The measures that the adornements are to be transfered
        between, (from adorned_measure, to unadorned_measure).

    Returns
    -------
    newly_adorned_measure : Measure
        The unadorned_measure with all its notes
        adorned with the adorned_measure's dynamic adornments

    Notes:
    Might want to look into having a dynamic tragectory

    """

    # find the length of the measure:
    calculate.calculate_measure_duration(adorned_measure)

    basic_data = read_basic_note_data(adorned_measure)

    dynamic_info = [[d[1] - adorned_measure.start_time, d[3]] for d in basic_data]
    adorned_note_start_times = [d[1] - adorned_measure.start_time for d in basic_data]
    # add accent information to the list:
    note = 0
    new_dynamic_info = []
    for info in dynamic_info:
        info = info + [
            adorned_measure.notes[note].adornment.plucking.accent,
            adorned_measure.notes[note].adornment.fretting.accent
        ]
        new_dynamic_info.append(info)
        note += 1
    #print(new_dynamic_info)

    # See if any of the notes in the unadorned measure line up:
    newly_adorned_measure = unadorned_measure
    for unadorned_note in unadorned_measure.notes:
        adorned_unadorned_note = unadorned_note
        corrected_unadorned_note_start_time = (
            unadorned_note.note.start_time - unadorned_measure.start_time)
        if (corrected_unadorned_note_start_time in adorned_note_start_times):
            adorned_note_index = adorned_note_start_times.index(
                corrected_unadorned_note_start_time)

            # update the dynamics, and accents to be
            # that of the adorned note

            adorned_note = adorned_measure.notes[adorned_note_index]

            adorned_unadorned_note = update.update_note_in_adorned_note(
                unadorned_note.note,
                unadorned_note,
                dynamic=adorned_note.note.dynamic)
            updated_adornment = update.update_plucking_in_adorment(
                adorned_unadorned_note.adornment.plucking,
                adorned_unadorned_note.adornment,
                accent=adorned_note.adornment.plucking.accent)
            updated_adornment = update.update_fretting_in_adornment(
                adorned_unadorned_note.adornment.fretting,
                updated_adornment,
                accent=adorned_note.adornment.fretting.accent)

            adorned_unadorned_note = update.update_adornment_in_adorned_note(
                adorned_unadorned_note.adornment,
                adorned_unadorned_note,
                fretting=updated_adornment.fretting,
                plucking=updated_adornment.plucking)

        # update the note in the measure:
        newly_adorned_measure = update.update_note_in_measure(
            unadorned_note, adorned_unadorned_note, newly_adorned_measure)

    return newly_adorned_measure


'''
def most_similar_note(unadorned_note, adorned_measure):
    """Find the most similar note in the adorned measure.

    """

    closest_note = None
    for adorned_note in adorned_measure.notes:
        if closest_note is None:
            closest_note = (adorned_note,
                            note_similarty(unadorned_note, adorned_note))
        else:
            if note_similarty(unadorned_note, adorned_note) < closest_note[1]:
                closest_note = (adorned_note,
                                note_similarty(unadorned_note, adorned_note))
    return closest_note[0]


def note_similarty(note1, note2):
    """Calculate the similarity between two notes

    Parameters
    ---------
    note1, note2 : AdornedNote
        the notes that the distance (euclidean) is calculated between
        using the pitch, fret, string and duration properties of each
        of the notes.

    Returns
    -------
    distance : float
        euclidean distance between the two notes

    """
    print(note1, note2)
    assert (isinstance(note1, AdornedNote) and isinstance(
        note2, AdornedNote)), ("One or more inputs are not type AdornedNote")

    distance = sqrt(
        pow((note1.note.pitch - note2.note.pitch), 2) +
        pow((note1.note.fret_number - note2.note.fret_number), 2) +
        pow((note1.note.string_number - note2.note.string_number), 2))
    return distance


'''


def adorned_note_sequence(from_unadorned_note, unadorned_sequence,
                          adorned_sequence):
    """Starting on from_unadorned_note in unadorned_measure
    make an interval sequence and find the longest sequence where
    the intervals are the most similar in adorned measure


    Parameters
    ---------
    from_unadorned_note : AdornedNote

    unadorned_measure, adorned_measure : Mesure


    Returns
    -------
    unadorned_notes_processed : list

    adorned_note_order : list

    """

    #unadorned_measure_no_tied_notes = calculate.calculate_tied_note_durations(
    #    unadorned_measure)
    #adorned_measure_no_tied_notes = calculate.calculate_tied_note_durations(
    #    adorned_measure)

    # strip out rests:
    #unadorned_measure_notes = []
    #for note in unadorned_measure_no_tied_notes:
    #    if isinstance(note, AdornedNote):
    #        unadorned_measure_notes.append(note)

    #adorned_measure_notes = []
    #for note in adorned_measure_no_tied_notes:
    #    if isinstance(note, AdornedNote):
    #        adorned_measure_notes.append(note)

    if from_unadorned_note == unadorned_sequence[-1]:
        #print("last note")
        return

    adorned_note_order = []
    unadorned_notes_processed = []

    # match the index based on the note_number:
    #note_numbers = map(lambda n: n.note.note_number, unadorned_sequence)
    unadorned_note_index = unadorned_sequence.index(from_unadorned_note)

    #unadorned_note_index = unadorned_measure.notes.index(from_unadorned_note)

    for n1, n2 in zip(unadorned_sequence[unadorned_note_index::],
                      unadorned_sequence[unadorned_note_index + 1::]):

        interval = n2.note.pitch - n1.note.pitch

        best_matching_adorned_interval = None
        for a1, a2 in zip(adorned_sequence[0::], adorned_sequence[1::]):
            adorned_forward_interval = a2.note.pitch - a1.note.pitch
            adorned_reverse_interval = a1.note.pitch - a2.note.pitch

            forward_dif = abs(interval - adorned_forward_interval)
            reverse_dif = abs(interval - adorned_reverse_interval)

            if min(forward_dif, reverse_dif) == forward_dif:
                best_matching_direction = [a1, a2]

            if min(forward_dif, reverse_dif) == reverse_dif:
                best_matching_direction = [a2, a1]

            if best_matching_adorned_interval is None:
                best_matching_adorned_interval = best_matching_direction
            else:
                best_interval = (best_matching_adorned_interval[1].note.pitch -
                                 best_matching_adorned_interval[0].note.pitch)
                best_direction_interval = (
                    best_matching_direction[1].note.pitch -
                    best_matching_direction[0].note.pitch)

                best_interval_dif = abs(interval - best_interval)
                best_direction_dif = abs(interval - best_direction_interval)

                # if the best matching direction is closer than the
                # best matching interval, make it the best matching interval.
                if min(best_interval_dif,
                       best_direction_dif) == best_direction_dif:
                    best_matching_adorned_interval = best_matching_direction

        if adorned_note_order == []:
            adorned_note_order += best_matching_adorned_interval

            if unadorned_notes_processed == []:
                unadorned_notes_processed.append(n1)
                unadorned_notes_processed.append(n2)
            elif unadorned_notes_processed[-1] == n1:
                unadorned_notes_processed.append(n2)

        else:
            # if this new best matching interval has the same starting
            # note that was previously added, add the second note
            # of the interval.
            if best_matching_adorned_interval[0] == adorned_note_order[-1]:
                adorned_note_order.append(best_matching_adorned_interval[1])
                if n1 in unadorned_notes_processed:
                    #print("adding n2")
                    unadorned_notes_processed.append(n2)
            else:
                #print("end of sequence")
                break

    return unadorned_notes_processed, adorned_note_order


def make_basic_notes(list_of_notes):
    """Take list of AdornedNotes and make them BasicNotes


    Note: only really used to debugging things.

    """

    return [BasicNote(ad_note.note.pitch, ad_note.note.start_time, ad_note.note.duration, ad_note.note.dynamic.value) for ad_note in list_of_notes]


def find_note_sequences(list_of_notes):
    """Find all sequences of notes that are not interrupted by rests

    """
    sequences = []
    seq = []
    for note in list_of_notes:
        if isinstance(note, AdornedNote):
            seq.append(note)
        elif isinstance(note, Rest):
            sequences.append(seq)
            seq = []

    return sequences


def chunk_up_a_measure(measure_or_notes_from_measure, chunk_size=3):
    """Break up a measure into chunks of AdornedNotes

    """

    if isinstance(measure_or_notes_from_measure, Measure):
        # get all the notes and tie together tied notes:
        notes = calculate.calculate_tied_note_durations(
            measure_or_notes_from_measure)

    if isinstance(measure_or_notes_from_measure, list):
        for n in measure_or_notes_from_measure:
            assert isinstance(n, AdornedNote)
        notes = measure_or_notes_from_measure

    # break the adorned measure into smaller chunks
    chunks = []
    last_note_added_to_a_chunk = False
    for note in notes:

        # check the note is not a rest:
        if isinstance(note, Rest):
            # if so continue:
            continue

        if last_note_added_to_a_chunk:
            # Reached the last note in the measure
            # so break
            break

        # start a new chunk:
        chunk = [note]

        for next_note in notes[notes.index(note)::]:
            if len(chunk) >= chunk_size:
                # start a new chunk:
                chunks.append(chunk)
                break
            # check the note is not a rest:
            if isinstance(next_note, Rest):
                # if so continue:
                continue

            # skip the starting note of the chunk:
            if next_note in chunk:
                continue

            chunk.append(next_note)

            if next_note == notes[-1]:
                last_note_added_to_a_chunk = True

        if chunk not in chunks:
            chunks.append(chunk)

    return chunks


def analyse_chunk(chunk, measure, chunk_id="chunk"):
    """Analyses the chunk from the measure
    with FANTASTIC and SynPy

    """
    try:
        chunk_midi = calculate.calculate_midi_file_for_measure_note_list(
            chunk, measure, midi_file_name=chunk_id)
        chunk_mcsv_file = utilities.run_melconv(
            chunk_midi,
            chunk_midi.split('.')[0] + ".csv")

        rhy_measure = Measure(measure.meta_data, measure.start_time, chunk)
        chunk_rhy = calculate.calculate_rhy_file_for_measure(
            rhy_measure, rhy_file_name=chunk_id + ".rhy")

        return chunk_midi, chunk_rhy, chunk_mcsv_file
    except:
        print("Error analysing chunk")
        return None, None, None


def match_up_unadorned_measure_chunks_with_adorned_measure_chunks(
        unadorned_measure, unadorned_measure_notes, adorned_measure,
        chunk_size=3):
    """Using FANTASTIC match up each unadorned note from the unadorned measure
    with adorned notes from the adorned measure that are most musically similar.

    returns:

    """

    assert isinstance(unadorned_measure,
                      Measure), "unadorned_measure must be a Measure"
    assert isinstance(adorned_measure,
                      Measure), "adorned_measure must be a Measure"

    # Load r related things:
    feature_analysis.fantastic_interface.load()

    # find what is smallest:
    chunk_size = min([
        len(unadorned_measure_notes),
        len(calculate.calculate_tied_note_durations(adorned_measure)),
        chunk_size
    ])

    print("chunksize:", chunk_size)
    assert chunk_size > 0

    unadorned_chunks = chunk_up_a_measure(unadorned_measure_notes, chunk_size)

    matched_unadorned_and_adorned_chunks = []

    # check the unadorned chunk sizes.
    unadored_chunk_sizes = [len(chunk) for chunk in unadorned_chunks]
    unadored_chunk_sizes = list(set(unadored_chunk_sizes))

    # Make a dict with the sizes as keys.
    chunk_size_dict = {}

    # setup the get_most_similar_adorned_chunk function and mix features:
    get_most_similar_adorned_chunk = r('''
                        get.most.similar.adorned.chunk <- function(measure.database.df, eucl.stand=TRUE, percent.match=0){

                            if(eucl.stand==TRUE){measure.database.df <- ztransform(measure.database.df)}

                            # get the features from the measure
                            features<-colnames(measure.database.df[,c(-1)])

                            rows <- measure.database.df$file.id[c(-1)]

                            database.df <- measure.database.df[c(-1),features]
                            rownames(database.df) <- rows
                            colnames(database.df) <- features

                            measure.df <- measure.database.df[1,features]
                            rownames(measure.df) <-  measure.database.df[1,1]

                            sim <- apply(database.df, 1, function(x)exp(-dist(rbind(x, measure.df))/length(features)))

                            sim.df <- data.frame(sim)
                            sim.df$file.id <- rownames(sim.df)

                            out <- as.numeric(sim.df$file.id[which(sim.df$sim >= max(sim.df$sim)-percent.match*max(sim.df$sim)/100)])

                            out
                            }
                    ''')

    mix_features = r('''
                        mix.features <- function(df1, df2){
                        rbind(df1, df2[, names(df1)])
                        }
                    ''')

    for c_size in unadored_chunk_sizes:
        # then chunk up the adorned measure, process it for each chunk size
        # add the adorned chunk dataframe into the dict.
        if c_size > 2:
            adorned_chunks = chunk_up_a_measure(adorned_measure, c_size)

            chunk_midi_files = []
            chunk_rhy_files = []
            chunk_mcsv_files = []

            chunk_index_id = 0
            for adorned_chunk in adorned_chunks:

                # adorned_chunk_id is just the index in the
                # adorned chunk list for easy retrieval later
                # adorned_chunk_id = str(adorned_chunks.index(adorned_chunk))

                chunk_midi, chunk_rhy, chunk_mcsv_file = analyse_chunk(
                    adorned_chunk, adorned_measure, str(chunk_index_id))

                chunk_index_id += 1

                #print('Adorned_chunk info:', chunk_midi, chunk_rhy,
                #      chunk_mcsv_file)

                if chunk_midi is None or chunk_rhy is None or chunk_mcsv_file is None:
                    continue

                chunk_midi_files.append(chunk_midi)
                chunk_rhy_files.append(chunk_rhy)
                chunk_mcsv_files.append(chunk_mcsv_file)

            # feature analysis:
            fantastic_formatted_chunk_mcsv_files = []

            for chunk_mcsv_file in chunk_mcsv_files:
                # format the mcsv list to be accepted by FANTASTIC:
                fantastic_formatted_chunk_mcsv_files.append(
                    chunk_mcsv_file.split(os.getcwd() + '/')[-1])

            # no mcsv files:
            if fantastic_formatted_chunk_mcsv_files == []:
                # Remove all the feature files:
                for midi_file, rhy_file, mcsv_file in zip(
                        chunk_midi_files, chunk_rhy_files, chunk_mcsv_files):
                    if os.path.isfile(midi_file):
                        os.remove(midi_file)
                    if os.path.isfile(rhy_file):
                        os.remove(rhy_file)
                    if os.path.isfile(os.path.basename(mcsv_file)):
                        os.remove(os.path.basename(mcsv_file))
                # then:
                continue

            adorned_chunks_feature_df = feature_analysis.merge_synpy_and_fantastic_features(
                fantastic_formatted_chunk_mcsv_files,
                chunk_rhy_files,
                rhy_table_output='_rhy_features.csv',
                save_location='_all_features.csv')

            # add the adorned chunk dataframe into the dict.
            chunk_size_dict[c_size] = (adorned_chunks,
                                       adorned_chunks_feature_df)

            for midi_file, rhy_file, mcsv_file in zip(
                    chunk_midi_files, chunk_rhy_files, chunk_mcsv_files):
                if os.path.isfile(midi_file):
                    os.remove(midi_file)
                if os.path.isfile(rhy_file):
                    os.remove(rhy_file)
                if os.path.isfile(os.path.basename(mcsv_file)):
                    os.remove(os.path.basename(mcsv_file))

        elif c_size == 2:
            adorned_chunks = chunk_up_a_measure(adorned_measure, c_size)

            feature_header = [
                'file.id', "p.range", "p.entropy", "p.std", "i.abs.range",
                "i.abs.mean", "i.abs.std", "i.mode", "i.entropy", "d.range",
                "d.median", "d.mode", "d.entropy", "len", "glob.duration",
                "note.dens", "PRS.mean_syncopation_per_bar",
                "KTH.mean_syncopation_per_bar", "LHL.mean_syncopation_per_bar",
                "SG.mean_syncopation_per_bar", "TMC.mean_syncopation_per_bar",
                "TOB.mean_syncopation_per_bar", "WNBD.mean_syncopation_per_bar"
            ]

            chunk_index_id = 0
            adorned_chunk_features = []
            for adorned_chunk in adorned_chunks:
                ac_features = analyse_two_note_chunk(adorned_chunk,
                                                     str(chunk_index_id),
                                                     adorned_measure)
                adorned_chunk_features.append(ac_features)
                chunk_index_id += 1

            # add the adorned chunk data into the dict.
            chunk_size_dict[c_size] = (adorned_chunks, adorned_chunk_features)

        elif c_size < 2:
            print('single note!')

    for unadorned_chunk in unadorned_chunks:
        # Make the chunks the same size as the adorned chunk:
        adorned_chunk_size = len(unadorned_chunk)
        if adorned_chunk_size > 2:

            # Analyse the unadorned chunk:
            ua_chunk_midi, ua_chunk_rhy, ua_chunk_mcsv_file = analyse_chunk(
                unadorned_chunk, unadorned_measure, "unadorned_chunk")

            unadorned_chunk_feature_df = feature_analysis.merge_synpy_and_fantastic_features(
                [ua_chunk_mcsv_file.split(os.getcwd() + '/')[-1]],
                [ua_chunk_rhy],
                rhy_table_output='_rhy_features.csv',
                save_location='_all_features.csv')

            # get the adorned chunk info:
            adorned_chunks, adorned_chunks_feature_df = chunk_size_dict.get(
                adorned_chunk_size)

            try:
                feature_df = mix_features(unadorned_chunk_feature_df,
                                          adorned_chunks_feature_df)
            except:
                # work out similarity based off of 2 note chunks:
                if 2 in list(chunk_size_dict.keys()):
                    adorned_chunks, adorned_chunk_features = chunk_size_dict[
                        adorned_chunk_size]
                else:
                    adorned_chunks = chunk_up_a_measure(
                        adorned_measure, c_size)

                    feature_header = [
                        'file.id', "p.range", "p.entropy", "p.std",
                        "i.abs.range", "i.abs.mean", "i.abs.std", "i.mode",
                        "i.entropy", "d.range", "d.median", "d.mode",
                        "d.entropy", "len", "glob.duration", "note.dens",
                        "PRS.mean_syncopation_per_bar",
                        "KTH.mean_syncopation_per_bar",
                        "LHL.mean_syncopation_per_bar",
                        "SG.mean_syncopation_per_bar",
                        "TMC.mean_syncopation_per_bar",
                        "TOB.mean_syncopation_per_bar",
                        "WNBD.mean_syncopation_per_bar"
                    ]

                    chunk_index_id = 0
                    adorned_chunk_features = []
                    for adorned_chunk in adorned_chunks:
                        ac_features = analyse_two_note_chunk(
                            adorned_chunk, str(chunk_index_id),
                            adorned_measure)
                        adorned_chunk_features.append(ac_features)
                        chunk_index_id += 1

                    # add the adorned chunk data into the dict.
                    chunk_size_dict[c_size] = (adorned_chunks,
                                               adorned_chunk_features)

                # break up the unadorned_chunk into chunks of 2
                for unadorned_note1, unadorned_note2 in zip(
                        unadorned_chunk[::], unadorned_chunk[1::]):
                    new_2_note_unadorned_chunk = [
                        unadorned_note1, unadorned_note2
                    ]
                    unadorned_chunk_features = analyse_two_note_chunk(
                        new_2_note_unadorned_chunk, 'unadorned_chunk',
                        unadorned_measure)

                    # write out the csv file that combines that features.
                    with open('2_note_features.csv', mode='w') as csv_file:
                        feature_writer = csv.writer(csv_file)
                        feature_writer.writerow(feature_header)
                        feature_writer.writerow(unadorned_chunk_features)
                        for ac_chunk in adorned_chunk_features:
                            feature_writer.writerow(ac_chunk)

                    del unadorned_chunk_features, adorned_chunk_features

                    # read in the csvfile as a dataframe and find most similar.
                    feature_df = feature_analysis.read_in_feature_dataframe(
                        "2_note_features.csv")

                    most_similar_adorned_chunk_indexes = get_most_similar_adorned_chunk(
                        feature_df)

                    most_similar_chunks = []
                    for chunk_index in most_similar_adorned_chunk_indexes:
                        most_similar_chunks.append(
                            adorned_chunks[int(chunk_index)])

                    matched_unadorned_and_adorned_chunks.append(
                        (new_2_note_unadorned_chunk, most_similar_chunks))

                    if os.path.isfile("2_note_features.csv"):
                        os.remove("2_note_features.csv")

                if os.path.isfile(ua_chunk_midi):
                    os.remove(ua_chunk_midi)
                if os.path.isfile(ua_chunk_rhy):
                    os.remove(ua_chunk_rhy)
                if os.path.isfile(os.path.basename(ua_chunk_mcsv_file)):
                    os.remove(os.path.basename(ua_chunk_mcsv_file))

                continue

            else:

                most_similar_adorned_chunk_indexes = (
                    get_most_similar_adorned_chunk(feature_df))

                most_similar_chunks = []
                for chunk_index in most_similar_adorned_chunk_indexes:
                    most_similar_chunks.append(
                        adorned_chunks[int(chunk_index)])

                matched_unadorned_and_adorned_chunks.append(
                    (unadorned_chunk, most_similar_chunks))

                del (most_similar_chunks, most_similar_adorned_chunk_indexes,
                     unadorned_chunk_feature_df, adorned_chunks, feature_df)

                if os.path.isfile(ua_chunk_midi):
                    os.remove(ua_chunk_midi)
                if os.path.isfile(ua_chunk_rhy):
                    os.remove(ua_chunk_rhy)
                if os.path.isfile(os.path.basename(ua_chunk_mcsv_file)):
                    os.remove(os.path.basename(ua_chunk_mcsv_file))

        elif adorned_chunk_size == 2:
            # get the unadorned features:
            unadorned_chunk_features = analyse_two_note_chunk(
                unadorned_chunk, 'unadorned_chunk', unadorned_measure)

            adorned_chunks, adorned_chunk_features = chunk_size_dict[
                adorned_chunk_size]

            # write out the csv file that combines that features.
            with open('2_note_features.csv', mode='w') as csv_file:
                feature_writer = csv.writer(csv_file)
                feature_writer.writerow(feature_header)
                feature_writer.writerow(unadorned_chunk_features)
                for ac_chunk in adorned_chunk_features:
                    feature_writer.writerow(ac_chunk)

            # read in the csvfile as a dataframe and find most similar.
            feature_df = feature_analysis.read_in_feature_dataframe(
                "2_note_features.csv")

            most_similar_adorned_chunk_indexes = (
                get_most_similar_adorned_chunk(feature_df))

            if os.path.isfile("2_note_features.csv"):
                os.remove("2_note_features.csv")

            most_similar_chunks = []
            for chunk_index in most_similar_adorned_chunk_indexes:
                most_similar_chunks.append(adorned_chunks[int(chunk_index)])

            matched_unadorned_and_adorned_chunks.append((unadorned_chunk,
                                                         most_similar_chunks))

            del (most_similar_chunks, most_similar_adorned_chunk_indexes,
                 unadorned_chunk_features, adorned_chunks)
            del feature_df, adorned_chunk_features

        else:
            print("single note!:")
            print(unadorned_chunk, adorned_measure)
            # single notes can't be processed/cause some issues:
            most_similar_notes = find_most_similar_notes(
                unadorned_chunk, adorned_measure)
            assert isinstance(most_similar_notes, list)
            most_similar_chunks = []
            for ms_note in most_similar_notes:
                assert isinstance(ms_note, list)
                #most_similar_chunks.append([ms_note])

            matched_unadorned_and_adorned_chunks.append((unadorned_chunk,
                                                         most_similar_notes))

            del most_similar_notes, most_similar_chunks

    if os.path.isfile('_rhy_features.csv'):
        os.remove('_rhy_features.csv')
    if os.path.isfile('_all_features.csv'):
        os.remove('_all_features.csv')
    """
    ua_ordered = []
    a_ordered = []
    for matched_chunk in matched_unadorned_and_adorned_chunks:

        ua_ordered.append(matched_chunk[0])
        a_ordered.append(matched_chunk[1])
    """

    del unadorned_chunks
    return [mua_a[0] for mua_a in matched_unadorned_and_adorned_chunks], [mua_a[1] for mua_a in matched_unadorned_and_adorned_chunks]


def analyse_two_note_chunk(chunk, chunk_id, measure):
    chunk_FANTASTIC_features = calculate.calculate_FANTASTIC_features_for_note_pair(
        chunk[0], chunk[1], measure)

    rhy_measure = Measure(measure.meta_data, measure.start_time, chunk)
    chunk_rhy = calculate.calculate_rhy_file_for_measure(
        rhy_measure, rhy_file_name=chunk_id + ".rhy")

    combined_features = feature_analysis.combine_synpy_and_fantastic_features_for_two_notes(
        measure, chunk, chunk_rhy, r_data_frame=False, save_table=False)

    #chunk_SynPy_features = feature_analysis.synpy_interface.compute_features(
    #    chunk_rhy)

    if os.path.isfile(chunk_rhy):
        os.remove(chunk_rhy)

    return combined_features

    # combine: chunk_FANTASTIC_features + chunk_SynPy_features
    # then return the list:
    return [
        chunk_SynPy_features[0], chunk_FANTASTIC_features["p.range"],
        chunk_FANTASTIC_features["p.entropy"],
        chunk_FANTASTIC_features["p.std"],
        chunk_FANTASTIC_features["i.abs.mean"],
        chunk_FANTASTIC_features["i.abs.std"],
        chunk_FANTASTIC_features["i.mode"],
        chunk_FANTASTIC_features["i.entropy"],
        chunk_FANTASTIC_features["d.range"],
        chunk_FANTASTIC_features["d.median"],
        chunk_FANTASTIC_features["d.mode"],
        chunk_FANTASTIC_features["d.entropy"], chunk_FANTASTIC_features["len"],
        chunk_FANTASTIC_features["glob.duration"],
        chunk_FANTASTIC_features["note.dens"]
    ] + chunk_SynPy_features[1:]


def find_most_similar_notes(unadorned_chunk, adorned_measure):
    """Find the most similar notes in the adorned_measure to the
    note in unadorned_chunk

    """

    assert len(unadorned_chunk) == 1, "Chunk doesn't contain only 1 note"
    assert isinstance(adorned_measure,
                      Measure), "adorned_measure is not type Measure"

    # get the tied not durations:
    adorned_measure_notes = calculate.calculate_tied_note_durations(
        adorned_measure)

    unadorned_note = unadorned_chunk[0]

    most_similar = None
    for adorned_note in adorned_measure_notes:
        if most_similar is None:
            most_similar = adorned_note

            dist_to_adorned_note = sqrt(
                pow(
                    unadorned_note.note.fret_number -
                    adorned_note.note.fret_number, 2) + pow(
                        unadorned_note.note.string_number -
                        adorned_note.note.string_number, 2) +
                pow(unadorned_note.note.pitch - adorned_note.note.pitch, 2) +
                pow(unadorned_note.note.duration -
                    adorned_note.note.duration, 2))

            most_similar = ([[adorned_note]], dist_to_adorned_note)

            continue

        dist_to_adorned_note = sqrt(
            pow(
                unadorned_note.note.fret_number -
                adorned_note.note.fret_number, 2) + pow(
                    unadorned_note.note.string_number -
                    adorned_note.note.string_number, 2) +
            pow(unadorned_note.note.pitch - adorned_note.note.pitch, 2) +
            pow(unadorned_note.note.duration - adorned_note.note.duration, 2))

        if dist_to_adorned_note < most_similar[1]:
            most_similar = ([[adorned_note]], dist_to_adorned_note)
        elif dist_to_adorned_note == most_similar[1]:
            most_similar[0].append([adorned_note])

    most_similar_return = most_similar[0]
    del adorned_measure_notes, most_similar

    return most_similar_return


def match_notes_based_on_closest_interval_sequences(unadorned_measure,
                                                    adorned_measure):
    """Matches the longest sequences of unadorned notes in
    the unadorned measure, with the closest matching sequences
    of adorned notes in the adorned measure. Then consolidates
    the adornedn notes that could match the unadorned ones and
    returns a of these.

    Parameters
    ---------
    unadorned_measure, adorned_measure : Measure

    Returns
    -------
    matched_notes : list of tuples
        tuples are in the form (unadorned_note, [adorned_note1, .... ])
        where the unadorned_note is a note from the unadorned_measure
        and adorned_note1, etc are adorned_notes from the
        adorned_measure that were found to match.


    """

    # get the adorned_notes to apply the adornments from:
    proced_ua_notes = []
    adorned_note_sequences = []
    unadorned_note_sequences = []

    # combine tied notes:
    combined_tied_unadorned_notes = calculate.calculate_tied_note_durations(
        unadorned_measure)
    combined_tied_adorned_notes = calculate.calculate_tied_note_durations(
        adorned_measure)

    # get sequences of notes with no rests:
    unadorned_note_seqs = find_note_sequences(combined_tied_unadorned_notes)
    adorned_note_seqs = find_note_sequences(combined_tied_adorned_notes)

    # make the named_tuple
    ClosestNotes = namedtuple("Closest", ["note1", "note2", "interval", "seq"])

    for unadorned_seq in unadorned_note_seqs:

        unadorned_matching_seq = []
        adorned_matching_seq = []

        pos_next_adorned_interval = None

        for unadorned_note in unadorned_seq:

            if unadorned_note == unadorned_seq[-1]:
                if unadorned_note in proced_ua_notes:
                    continue
                else:
                    closest_note = find_closest_notes(unadorned_note,
                                                      adorned_measure)
                    # add all the matching notes in a way that can be
                    # processed but the match up loop later:
                    for note in closest_note:
                        adorned_note_sequences.append([note])
                        unadorned_note_sequences.append([unadorned_note])
                    proced_ua_notes.append(unadorned_note)
            else:

                #find closest interval:

                un_n_index = unadorned_seq.index(unadorned_note)
                for un1, un2 in zip(unadorned_seq[un_n_index::],
                                    unadorned_seq[un_n_index + 1::]):
                    ua_interval = un1.note.pitch - un2.note.pitch

                    closest_notes = None

                    for adorned_seq in adorned_note_seqs:
                        if len(adorned_seq) > 1:
                            for an1, an2 in zip(adorned_seq[::],
                                                adorned_seq[1::]):
                                a_interval = an1.note.pitch - an2.note.pitch

                                if closest_notes is None:
                                    closest_notes = ClosestNotes(
                                        note1=an1,
                                        note2=an2,
                                        interval=a_interval,
                                        seq=adorned_seq)
                                else:
                                    if (abs(
                                            abs(a_interval) - abs(ua_interval))
                                            < abs(
                                                abs(closest_notes.interval) -
                                                abs(ua_interval))):
                                        # update the closest note:
                                        closest_notes = ClosestNotes(
                                            note1=an1,
                                            note2=an2,
                                            interval=a_interval,
                                            seq=adorned_seq)

                    #if pos_next_adorned_interval is not None:
                    #    if closest_notes.note1 == pos_next_adorned_interval.note1 or pos_next_adorned_interval.note2:
                    #        if closest_notes.note2 == pos_next_adorned_interval.note1 or pos_next_adorned_interval.note2:
                    #            print("same!")
                    if pos_next_adorned_interval is None:
                        print("Start new adorned_note sequnece")
                        unadorned_note_sequences.append(unadorned_matching_seq)
                        unadorned_matching_seq = []
                        adorned_note_sequences.append(adorned_matching_seq)
                        adorned_matching_seq = []

                    # got the closest interval + seq its in:
                    # work out the next possible one:
                    forward = closest_notes.note1 - closest_notes.note2
                    backwards = closest_notes.note2 - closest_notes.note1

                    foward_diff = abs(interval - forward)
                    backwards_diff = abs(interval - backwards)

                    if min(forward_dif, reverse_dif) == forward_dif:
                        print("forwards")

                        if closest_notes.note1 not in adorned_matching_seq:
                            adorned_matching_seq.append(closest_notes.note1)
                        if closest_notes.note2 not in adorned_matching_seq:
                            adorned_matching_seq.append(closest_notes.note)

                        remaining_notes = closest_notes.seq[
                            closest_notes.seq.index(closest_notes.note2)::]

                        if len(remaining_notes) > 1:
                            pos_next_adorned_interval = ClosestNotes(
                                note1=closest_notes.note2,
                                note2=closest_notes.seq[
                                    closest_notes.seq.index(
                                        closest_notes.note2) + 1],
                                interval=closest_notes.note2 -
                                closest_notes.seq[closest_notes.seq.index(
                                    closest_notes.note2) + 1],
                                seq=closest_notes.seq)

                        else:
                            pos_next_adorned_interval = None

                    if min(forward_dif, reverse_dif) == reverse_dif:
                        print('backwards')
                        if closest_notes.note2 not in adorned_matching_seq:
                            adorned_matching_seq.append(closest_notes.note2)
                        if closest_notes.note1 not in adorned_matching_seq:
                            adorned_matching_seq.append(closest_notes.note1)

                        if closest_notes.seq.index(closest_notes.note1) > 0:
                            pos_next_adorned_interval = ClosestNotes(
                                note1=closest_notes.note1,
                                note2=closest_notes.seq[
                                    closest_notes.seq.index(
                                        closest_notes.note1) - 1],
                                interval=closest_notes.note1 -
                                closest_notes.seq[closest_notes.seq.index(
                                    closest_notes.note1) - 1],
                                seq=closest_notes.seq)
                        else:
                            pos_next_adorned_interval = None

                    if un1 not in unadorned_matching_seq:
                        unadorned_matching_seq.append(un1)
                    if un2 not in unadorned_matching_seq:
                        unadorned_matching_seq.append(un2)
                    if un1 not in proced_ua_notes:
                        proced_ua_notes.append(un1)
                    if un2 not in proced_ua_notes:
                        proced_ua_notes.append(un2)

                #proc_ua_notes, ad_note_seq = adorned_note_sequence(
                #    unadorned_note, unadorned_measure, adorned_measure)

                #adorned_note_sequences.append(ad_note_seq)
                #unadorned_note_sequences.append(proc_ua_notes)
        unadorned_note_sequences.append(unadorned_matching_seq)
        unadorned_matching_seq = []
        adorned_note_sequences.append(adorned_matching_seq)
        adorned_matching_seq = []
    """
    # match up unadorned notes with adorned ones:
    matched_notes = []
    for unadorned_seq, adorned_seq in zip(unadorned_note_sequences,
                                          adorned_note_sequences):
        # just to debug make them basic notes:
        # unadorned_seq = make_basic_notes(unadorned_seq)
        # adorned_seq = make_basic_notes(adorned_seq)
        for unadorned, adorned in zip(unadorned_seq, adorned_seq):
            matched_pair = (unadorned, [adorned])

            # if the unadorned not has already been matched:
            # add more adorned notes to the adorned not part
            # of the tuple.
            notes_already_matched = map(lambda n: n[0], matched_notes)
            if unadorned in notes_already_matched:
                index = notes_already_matched.index(unadorned)
                # don't add duplicate adorned notes:
                if adorned not in matched_notes[index][1]:
                    matched_notes[index][1].append(adorned)
            else:
                matched_notes.append(matched_pair)

    """
    del combined_tied_unadorned_notes, combined_tied_adorned_notes

    return unadorned_note_sequences, adorned_note_sequences


def consolidate_note_sequnces_matches_to_note_matches(unadorned_note_sequences,
                                                      adorned_note_sequences):
    """Match up all the aligned notes in the sequences returning a
    list of tuples in the form (unadorned note, [adorned notes that match])

    Parameters:
    ---------
    unadorned_note_sequences, adorned_note_sequences : list of lists
        normally output from match_notes_based_on_closest_interval_sequences

    Returns:
    -------
    matched_notes : list of tuples
        list of tuples that give the unadorned note and a list of
        all the adorned notes that match it in the following form:
        (unadorned note, [adorned notes that match])
    """

    matched_notes = []
    matched_au_a = namedtuple("Matched", ['unadorned_note', 'adorned_notes'])

    for ua_chunk, matched_chunks in zip(unadorned_note_sequences,
                                        adorned_note_sequences):

        for matched_chunk in matched_chunks:
            #if isinstance(matched_chunk, AdornedNote):
            #    matched_chunk = [matched_chunk]

            for ua_note, a_note in zip(ua_chunk, matched_chunk):
                ua_notes_already_matched = [m.unadorned_note for m in matched_notes]
                if ua_note not in ua_notes_already_matched:
                    matched_notes.append(matched_au_a(ua_note, [a_note]))

                elif ua_note in ua_notes_already_matched:
                    print("already matched!")
                    print("index = ", ua_notes_already_matched.index(ua_note))

                    print("has adorned_notes:",
                          [m.note.note_number for m in matched_notes[ua_notes_already_matched.index(
                                  ua_note)].adorned_notes])

                    matched_notes[ua_notes_already_matched.index(
                        ua_note)].adorned_notes.append(a_note)

    del unadorned_note_sequences, adorned_note_sequences

    return matched_notes


def get_interval_relative_to_key_sig(adorned_note, key_signature):
    # get the key_signature:
    tonic = "C"
    mode = "Major"
    if key_signature.find("Major"):
        tonic = "".join(map(str, key_signature.split("Major")))
        mode = "Major"
    elif key_signature.find("Minor"):
        tonic = "".join(map(str, key_signature.split("Minor")))
        mode = "Minor"

    if tonic.find("Flat"):
        # convert the tonic to only sharps:
        tonic_to_note_letter = {
            "AFlat": "G#",
            "BFlat": "A#",
            "CFlat": "B",
            "DFlat": "C#",
            "EFlat": "D#",
            "FFlat": "E",
            "GFlat": "F#"
        }
        tonic = tonic_to_note_letter.get(tonic)
    if tonic.find("Sharp"):
        tonic = tonic.split("Sharp")[0] + "#"

    note_letter = utilities.midinumber2letter(adorned_note.note.pitch)

    key_notes = utilities.reorder_note_letters_to_tonic(tonic)

    return key_notes.index(note_letter)


def adorn_unadorned_note(unadorned_note,
                         adorned_notes,
                         unadorned_measure,
                         adorned_measure,
                         complexity_weight,
                         difficulty_weight,
                         weight_set,
                         gp5_wellformedness=True
                         #adornment_selection_method
                         ):
    """Adorn the unadorned note with adornements from the
    adorned notes.

    Parameters
    ---------
    unadorned_note : AdornedNote
        Unadorned note that needs to have its adornements updated

    adorned_notes : list of AdornedNotes
        list of the possible adorned_notes that can have their
        adornments applied to the adorned note.

    unadorned_measure, adorned_measure : Measure
        the measures where the unadorned and adorned notes came from

    complexity_weight, difficulty_weight : -1 to 1
        Sets the weighting for the complexity and difficulty values
        for the newly_adorned_note selection criteria.
        0 means the value is ignored
        +ve numbers mean the value is maximised.
        -ve the value is minimised.

    gp5_wellformedness : boolean
        Set True to restrict the adornments to be wellformed for gp5
        file format. Set False to allow for any possible combination
        following the bass playing ontology.

    Returns
    -------
    AdornedNote
        best possible combination of the unadorned and possible adornments
        according to the complexity and difficulty weights

    """

    assert isinstance(unadorned_note,
                      AdornedNote), "unadorned_note is not type AdornedNote"

    assert isinstance(adorned_notes, list), "adorned_notes is not a list"

    pa = find_all_possible_adornements(unadorned_note, adorned_notes,
                                       unadorned_measure, adorned_measure)
    possible_adornments = make_all_possible_adornments(
        pa.plucking_accents,
        pa.fretting_accents,
        pa.plucking_techniques,
        pa.plucking_modifications_ah,
        pa.plucking_modifications_palm_mute,
        pa.fretting_techniques,
        pa.fretting_modifications_type,
        pa.fretting_modifications_let_ring,
        pa.fretting_modulations_bend,
        pa.fretting_modulations_trill,
        pa.fretting_modulations_vib,
        pa.fretting_modulations_slide,
        pa.grace_notes,
        pa.ghost_notes,
        complexity_weight=complexity_weight,
        difficulty_weight=difficulty_weight,
        gp5_wellformedness=True,
    )
    #print("possible_adornments: ", possible_adornments)

    # select and return the best possible newly_adorned_note:
    return select_best_adornment_for_unadorned_note(
        unadorned_note, possible_adornments, pa.dynamics, unadorned_measure,
        complexity_weight, difficulty_weight, weight_set)


def select_best_adornment_for_unadorned_note(
        unadorned_note, possible_adornments, possible_dynamics,
        unadorned_measure, complexity_weight, difficulty_weight, weight_set):

    unadorned_note_in = unadorned_note
    unadorned_note = unadorned_note.note

    print('possible notes: ',
          len(possible_adornments) * len(possible_dynamics))

    selected = namedtuple("Selected",
                          ["newly_adorned_note", 'complexity', "difficulty"])
    selected_newly_adorned_note = None
    for adornment in possible_adornments:
        # work out what one to pick here.....
        #print(adornment)
        # need to update the dynamic in unadorned_note...
        for d in possible_dynamics:
            #print("with dynamic added")
            dynamic_unadorned_note = Note(
                note_number=unadorned_note.note_number,
                pitch=unadorned_note.pitch,
                fret_number=unadorned_note.fret_number,
                string_number=unadorned_note.string_number,
                string_tuning=unadorned_note.string_tuning,
                start_time=unadorned_note.start_time,
                duration=unadorned_note.duration,
                notated_duration=unadorned_note.notated_duration,
                dynamic=d)
            #print(AdornedNote(dynamic_unadorned_note, adornment))

            adorned_note = AdornedNote(dynamic_unadorned_note, adornment)

            # some quick checks:
            assert isinstance(adorned_note.adornment.fretting.modulation,
                              Modulation), "Modulation adornment is wrong"

            ####################################

            # calculating musiplectic stuff:
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

            assert isinstance(use_geometric_mean, bool)
            assert isinstance(use_total_playing_time, bool)
            assert isinstance(log_scale_values, bool)

            # set some default values:

            playing_technique_complexity = 0
            duration_tempo_complexity = 0
            time_sig_complexity = 0
            bpm_complexity = 0
            expressive_techniques_complexity = 0
            articulations_accents_complexity = 0
            dynamics_complexity = 0
            key_sig_complexity = 0
            fret_playing_postion_complexity = 0
            shift_distance_complexity = 0
            note_playing_complexity = 0

            interval_complexity = 0
            interval_ioi_complexity = 0
            shift_distance_complexity = 0
            interval_dynamic_complexity = 0
            interval_fret_position_complexity = 0
            interval_expression_complexity = 0

            # get measure stuff:
            time_sig = unadorned_measure.meta_data.time_signature
            bpm = unadorned_measure.meta_data.tempo
            key_sig = unadorned_measure.meta_data.key_signature

            playing_techniques = calculate.calculate_musiplectic_techniques(
                adorned_note)
            '''
            if adorned_note.note.duration == 0:
                if adorned_note.note.notated_duration.value != 0:
                    rt_duration = calculate_realtime_duration(
                        adorned_note.note.notated_duration.value, bpm)
            else:
            '''

            # first see if there is a grace_note:
            previous_note = None
            new_adorned_note = adorned_note

            #if adorned_note.adornment.grace_note is not None:
            #    #print("grace_note!")
            #    adorned_note_list = calculate.calculate_grace_note_possitions(
            #        [adorned_note])
            #    previous_note = grace_note_list[0]
            #    adorned_note = grace_note_list[1]

            adorned_note_list = calculate.calculate_grace_note_possitions(
                [adorned_note])

            for adorned_note in adorned_note_list:
                ## Techniques:
                rt_duration = calculate.calculate_realtime_duration(
                    adorned_note.note.duration, bpm)
                #duration_tempo = calculate_musiplectics_duration(adorned_note, bpm)
                expressive_techniques = calculate.calculate_musiplectic_expression(
                    adorned_note)
                articulations_accents = calculate.calculate_musiplectic_articulations(
                    adorned_note)
                dynamic = calculate.calculate_musiplectic_dynamic(adorned_note)
                fret_playing_postion = calculate.calculate_musiplectic_fret_possition(
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

                playing_technique_complexity += reduce(
                    mul, playing_technique_note_scores)

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

                bpm_musiplectic = calculate.calculate_closest_value(
                    bpm_list, bpm)

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

                expressive_techniques_complexity += reduce(
                    mul, expressive_techniques_score)

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

                articulations_accents_complexity += reduce(
                    mul, articulations_accent_score)

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

                dynamics_complexity += reduce(mul, dynamic_score)

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

                shift_distance_score = musiplectics.shifting_weights(
                    use_geometric_mean=use_geometric_mean,
                    use_total_playing_time=use_total_playing_time,
                    log_scale_values=log_scale_values).get(str(0))

                shift_distance_complexity += shift_distance_score

                # Adapting the Musiplectics original equation:
                # fret_position x technique x expression x articulation x
                #       dynamic x duration x timesig x bpm
                note_playing_complexity += (fret_position_score * reduce(
                    mul, playing_technique_note_scores) * reduce(
                        mul, expressive_techniques_score) * reduce(
                            mul, articulations_accent_score) * reduce(
                                mul, dynamic_score) * duration_tempo_score *
                                            time_sig_score * bpm_score)

                if previous_note is not None:
                    interval = calculate.calculate_pitch_interval(
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
                    interval_ioi_rt_duration = calculate.calculate_realtime_duration(
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
                        interval_fret_position = calculate.calculate_musiplectic_fret_possition(
                            adorned_note)
                    elif adorned_note.note.fret_number < previous_note.note.fret_number:
                        interval_fret_position = calculate.calculate_musiplectic_fret_possition(
                            previous_note)

                    interval_fret_position_score = musiplectics.fret_position_weights(
                        use_geometric_mean=use_geometric_mean,
                        use_total_playing_time=use_total_playing_time,
                        log_scale_values=log_scale_values).get(
                            interval_fret_position)
                    interval_fret_position_complexity += interval_fret_position_score

                    interval_complexity += (
                        interval_score * interval_ioi_score * key_sig_score *
                        interval_dynamic_score * shift_distance_score *
                        interval_fret_position_score *
                        interval_expression_score)

            playing_complexity_vector = [
                playing_technique_complexity, duration_tempo_complexity,
                bpm_score, key_sig_complexity, time_sig_complexity,
                expressive_techniques_complexity,
                articulations_accents_complexity, dynamics_complexity,
                fret_playing_postion_complexity, interval_complexity,
                interval_ioi_complexity, shift_distance_complexity,
                interval_dynamic_complexity, interval_fret_position_complexity,
                interval_expression_complexity
            ]

            playing_complexity = sum(
                [note_playing_complexity, interval_complexity])
            percieved_difficulty = calculate.calculate_euclidean_complexity(
                playing_complexity_vector)

            #print("Complexity=", playing_complexity)
            #print("Difficulty=", percieved_difficulty)

            # decide what note to select:
            if selected_newly_adorned_note is None:
                selected_newly_adorned_note = selected(
                    new_adorned_note, note_playing_complexity,
                    percieved_difficulty)
            else:
                if (((playing_complexity - selected_newly_adorned_note.
                      complexity) * complexity_weight +
                     (percieved_difficulty - selected_newly_adorned_note.
                      difficulty) * difficulty_weight) >= 0):
                    selected_newly_adorned_note = selected(
                        new_adorned_note, note_playing_complexity,
                        percieved_difficulty)

    return selected_newly_adorned_note.newly_adorned_note


def make_all_possible_adornments(plucking_accents,
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
                                 complexity_weight,
                                 difficulty_weight,
                                 gp5_wellformedness=True):

    # combine artificial harmonics, natural-harmonics and deadnotes:
    dn_ah_ns = []
    for a in plucking_modifications_ah + fretting_modifications_type:
        if a not in dn_ah_ns:
            dn_ah_ns.append(a)

    # set if let ring and ghost notes:
    # basically if the complexity or difficulty weights are negative
    # then these adornments shouldn't be set:
    if ((complexity_weight == 0 and difficulty_weight < 0)
            or (complexity_weight < 0 and difficulty_weight == 0)
            or (complexity_weight < 0 and difficulty_weight < 0)):
        f_mod_lr = False
        ghost_n = False
    else:
        f_mod_lr = fretting_modifications_let_ring
        ghost_n = ghost_notes

    possible_adornments = []
    for grace_n in grace_notes:
        for p_tech in plucking_techniques:
            for f_tech in fretting_techniques:
                for p_mod_pm in plucking_modifications_palm_mute:
                    for p_accent in plucking_accents:
                        for f_accent in fretting_accents:
                            for vib in fretting_modulations_vib:
                                for bend in fretting_modulations_bend:
                                    for trill in fretting_modulations_trill:
                                        if (p_tech == 'tap'
                                                and gp5_wellformedness):
                                            trill = None

                                        if (isinstance(trill, Trill)
                                                and gp5_wellformedness):

                                            # can't have these with a trill:
                                            slide = None
                                            f_mod_type = None
                                            p_mod_ah = None

                                            adornment = Adornment(
                                                PluckingAdornment(
                                                    p_tech,
                                                    PluckingModification(
                                                        p_mod_pm, p_mod_ah),
                                                    p_accent),
                                                FrettingAdornment(
                                                    technique=f_tech,
                                                    modification=
                                                    FrettingModification(
                                                        type=f_mod_type,
                                                        let_ring=f_mod_lr),
                                                    accent=f_accent,
                                                    modulation=Modulation(
                                                        bend, vib, trill,
                                                        slide)),
                                                grace_note=grace_n,
                                                ghost_note=ghost_n)

                                            if adornment not in possible_adornments:
                                                possible_adornments.append(
                                                    adornment)

                                        # can't have slide, trill or any
                                        # dead_notes and harmonics:
                                        trill = None
                                        for slide in fretting_modulations_slide:
                                            for dn_ah_n in dn_ah_ns:
                                                f_mod_type = dn_ah_n
                                                p_mod_ah = None
                                                if dn_ah_n == 'dead-note':
                                                    f_mod_type = dn_ah_n
                                                    p_mod_ah = None
                                                    if grace_n is not None:
                                                        g_n_transition = grace_n.transition

                                                        if grace_n.dead_note:
                                                            if grace_n.transition == 'slide':
                                                                g_n_transition = None

                                                        if grace_n.transition == 'bend':
                                                            g_n_transition = None

                                                        grace_n = GraceNote(
                                                            fret=grace_n.fret,
                                                            duration=grace_n.
                                                            duration,
                                                            dynamic=grace_n.
                                                            dynamic,
                                                            dead_note=grace_n.
                                                            dead_note,
                                                            on_beat=grace_n.
                                                            on_beat,
                                                            transition=
                                                            g_n_transition)

                                                    if f_tech == 'hammer-on' and gp5_wellformedness:
                                                        f_mod_type = None
                                                    if f_tech == 'pull-off' and gp5_wellformedness:
                                                        f_mod_type = None
                                                if dn_ah_n == 'natural-harmonic':
                                                    f_mod_type = dn_ah_n
                                                    p_mod_ah = None

                                                    if grace_n is not None:
                                                        if grace_n.transition != 'bend':
                                                            grace_n = GraceNote(
                                                                fret=grace_n.
                                                                fret,
                                                                duration=
                                                                grace_n.
                                                                duration,
                                                                dynamic=grace_n.
                                                                dynamic,
                                                                dead_note=
                                                                grace_n.
                                                                dead_note,
                                                                on_beat=grace_n.
                                                                on_beat,
                                                                transition=None
                                                            )

                                                    if p_tech == 'tap' and gp5_wellformedness:
                                                        f_mod_type = None
                                                if isinstance(
                                                        dn_ah_n,
                                                        ArtificialHarmonic):
                                                    p_mod_ah = dn_ah_n
                                                    f_mod_type = None
                                                    if grace_n is not None:
                                                        if grace_n.transition != 'bend':
                                                            grace_n = GraceNote(
                                                                fret=grace_n.
                                                                fret,
                                                                duration=
                                                                grace_n.
                                                                duration,
                                                                dynamic=grace_n.
                                                                dynamic,
                                                                dead_note=
                                                                grace_n.
                                                                dead_note,
                                                                on_beat=grace_n.
                                                                on_beat,
                                                                transition=None
                                                            )
                                                    if p_tech == 'tap' and gp5_wellformedness:
                                                        p_mod_ah = None

                                                adornment = Adornment(
                                                    PluckingAdornment(
                                                        p_tech,
                                                        PluckingModification(
                                                            p_mod_pm,
                                                            p_mod_ah),
                                                        p_accent),
                                                    FrettingAdornment(
                                                        technique=f_tech,
                                                        modification=
                                                        FrettingModification(
                                                            type=f_mod_type,
                                                            let_ring=f_mod_lr),
                                                        accent=f_accent,
                                                        modulation=Modulation(
                                                            bend, vib, trill,
                                                            slide)),
                                                    grace_note=grace_n,
                                                    ghost_note=ghost_n)
                                                if adornment not in possible_adornments:
                                                    possible_adornments.append(
                                                        adornment)

    return possible_adornments


def find_all_possible_adornements(unadorned_note, adorned_notes,
                                  unadorned_measure, adorned_measure):

    # make lists of all the possible adornments for each type of adornment
    # from all of the possible notes.
    # before a possible adornment is added it needs to be checked/adapted
    # in the right way to be used, or it is not presented as a possible adornment

    #unadorned_note_in = unadorned_note
    unadorned_note = unadorned_note.note

    dynamics = []
    plucking_accents = []
    fretting_accents = []

    plucking_techniques = []
    plucking_modifications_ah = []
    plucking_modifications_palm_mute = []

    fretting_techniques = []
    fretting_modifications_type = []
    fretting_modifications_let_ring = False

    fretting_modulations_bend = []
    fretting_modulations_trill = []
    fretting_modulations_vib = []
    fretting_modulations_slide = []

    grace_notes = []
    ghost_notes = False

    for adorned_note in adorned_notes:
        assert isinstance(
            adorned_note,
            AdornedNote), "one of the adorned_notes is not type AdornedNote"

        adorned_measure_downbeat = Fraction(
            1, int(adorned_measure.meta_data.time_signature.split("/")[-1]))
        unadorned_measure_downbeat = Fraction(
            1, int(unadorned_measure.meta_data.time_signature.split("/")[-1]))

        # seeing if then notes fall on the same type of beat, relative
        # to the downbeat of each measure:
        # then accent adornments are added to the lists:
        if ((unadorned_note.start_time - unadorned_measure.start_time) %
                unadorned_measure_downbeat ==
            (adorned_note.note.start_time - adorned_measure.start_time) %
                adorned_measure_downbeat):
            plucking_accents.append(adorned_note.adornment.plucking.accent)
            fretting_accents.append(adorned_note.adornment.fretting.accent)
        else:
            # default is no accent:
            if False not in plucking_accents:
                plucking_accents.append(False)
            if False not in fretting_accents:
                fretting_accents.append(False)

        # see if the note duration has a similar relationship to
        # the length of the measure it is in:
        # and adding adornments that are related to this property
        # to the right lists.
        if (unadorned_note.duration / calculate.calculate_measure_duration(
                unadorned_measure) == adorned_note.note.duration /
                calculate.calculate_measure_duration(adorned_measure)) or (
                    unadorned_note.notated_duration.value /
                    calculate.calculate_measure_duration(unadorned_measure) ==
                    adorned_note.note.notated_duration.value /
                    calculate.calculate_measure_duration(adorned_measure)):

            if adorned_note.adornment.fretting.modulation.trill is not None:

                # converting the trill adornment:
                trill_interval = (
                    adorned_note.adornment.fretting.modulation.trill.fret -
                    adorned_note.note.fret_number)
                if adorned_note.adornment.fretting.modulation.trill.notated_duration.value is not None:
                    trill_duration_ratio = (
                        adorned_note.note.notated_duration.value /
                        adorned_note.adornment.fretting.modulation.trill.
                        notated_duration.value)
                else:
                    # if there is no trill duration just make it trill twice:
                    trill_duration_ratio = 4

                trill_duration = NotatedDuration(
                    unadorned_note.notated_duration.value /
                    trill_duration_ratio, adorned_note.adornment.fretting.
                    modulation.trill.notated_duration.isDotted,
                    adorned_note.adornment.fretting.modulation.trill.
                    notated_duration.isDoubleDotted, adorned_note.adornment.
                    fretting.modulation.trill.notated_duration.tuplet)

                trill_fret = trill_interval + unadorned_note.fret_number

                if trill_fret < 0:
                    if Trill(0,
                             trill_duration) not in fretting_modulations_trill:
                        fretting_modulations_trill.append(
                            Trill(0, trill_duration))
                else:
                    if Trill(trill_fret,
                             trill_duration) not in fretting_modulations_trill:
                        fretting_modulations_trill.append(
                            Trill(trill_fret, trill_duration))
            else:
                if None not in fretting_modulations_trill:
                    fretting_modulations_trill.append(None)

            if adorned_note.adornment.fretting.modulation.bend not in fretting_modulations_bend:
                fretting_modulations_bend.append(
                    adorned_note.adornment.fretting.modulation.bend)
            if adorned_note.adornment.fretting.modulation.vibrato not in fretting_modulations_vib:
                fretting_modulations_vib.append(
                    adorned_note.adornment.fretting.modulation.vibrato)

        else:
            if None not in fretting_modulations_trill:
                fretting_modulations_trill.append(None)
            if None not in fretting_modulations_bend:
                fretting_modulations_bend.append(None)
            if False not in fretting_modulations_vib:
                fretting_modulations_vib.append(False)

        # check open strings for slides.
        adorned_slide = adorned_note.adornment.fretting.modulation.slide

        if adorned_slide is not None:
            into = adorned_slide.into
            outto = adorned_slide.outto
            if unadorned_note.fret_number == 0:
                outto = None
                if adorned_slide.into == 'slide_from_below':
                    into = None

            if into is None and outto is None:
                adorned_slide = None
            else:
                adorned_slide = Slide(into, outto)

        if adorned_slide not in fretting_modulations_slide:
            fretting_modulations_slide.append(
                adorned_note.adornment.fretting.modulation.slide)

        # add the dynamic info to the lists:
        if adorned_note.note.dynamic not in dynamics:
            dynamics.append(adorned_note.note.dynamic)

        # Dealing with plucking adornments:
        if adorned_note.adornment.plucking.technique not in plucking_techniques:
            plucking_techniques.append(
                adorned_note.adornment.plucking.technique)

        if adorned_note.adornment.plucking.modification.palm_mute not in plucking_modifications_palm_mute:
            plucking_modifications_palm_mute.append(
                adorned_note.adornment.plucking.modification.palm_mute)

        if adorned_note.adornment.plucking.modification.artificial_harmonic is not None:
            # check to see if the note can be played as an
            # artificial harmonic without changing its pitch
            pos_ahs = possible_artificial_harmonic_pitches(
                unadorned_note.string_tuning)
            if unadorned_note.pitch in list(pos_ahs.keys()):

                ah = ArtificialHarmonic(
                    guitarpro.models.Octave(
                        pos_ahs[unadorned_note.pitch][0].ah[0]),
                    guitarpro.models.PitchClass(unadorned_note.pitch))

                if ah not in plucking_modifications_ah:
                    plucking_modifications_ah.append(ah)
            else:
                if None not in plucking_modifications_ah:
                    plucking_modifications_ah.append(None)
        else:
            if None not in plucking_modifications_ah:
                plucking_modifications_ah.append(None)

        # Dealing with fretting adornments:

        # stop fretting an open string and vice versa:
        if adorned_note.adornment.fretting.technique == 'fretting' and adorned_note.note.fret_number == 0:
            if None not in fretting_techniques:
                fretting_techniques.append(None)
        elif adorned_note.adornment.fretting.technique is None and adorned_note.note.fret_number > 0:
            if 'fretting' not in fretting_techniques:
                fretting_techniques.append('fretting')
        elif adorned_note.adornment.fretting.technique not in fretting_techniques:
            fretting_techniques.append(
                adorned_note.adornment.fretting.technique)

        if adorned_note.adornment.fretting.modification.type not in fretting_modifications_type:
            if adorned_note.adornment.fretting.modification.type == 'natural-harmonic':
                # see if the pitch of the note can also be a natural harmonic:
                if unadorned_note.pitch in list(possible_natural_harmonic_pitches(
                        unadorned_note.string_tuning).keys()):
                    fretting_modifications_type.append(
                        adorned_note.adornment.fretting.modification.type)
                else:
                    if None not in fretting_modifications_type:
                        fretting_modifications_type.append(None)
            else:
                fretting_modifications_type.append(
                    adorned_note.adornment.fretting.modification.type)
        # Grace notes:
        if adorned_note.adornment.grace_note is not None:

            grace_note_interval = (adorned_note.adornment.grace_note.fret -
                                   adorned_note.note.fret_number)

            grace_note_fret = grace_note_interval + unadorned_note.fret_number

            grace_note_transision = adorned_note.adornment.grace_note.transition

            # prevent negative grace_notes:
            if grace_note_fret < 0:
                grace_note_fret = 0

            if grace_note_fret == 0:
                if grace_note_transision == 'bend':
                    grace_note_transision = None

            if grace_note_interval == 0:

                if grace_note_transision == 'slide' or grace_note_transision == 'hammer':
                    grace_note_transision = None

            # can't pull off from a dead_note:
            if adorned_note.adornment.grace_note.dead_note:
                if grace_note_transision == 'hammer':
                    if adorned_note.adornment.grace_note.fret > adorned_note.note.fret_number:
                        grace_note_transision = None
                if grace_note_transision == 'bend':
                    grace_note_transision = None


            """
            grace_note_duration = (unadorned_note.duration * (
                adorned_note.adornment.grace_note.duration /
                adorned_note.note.duration))

            # correct if it is great than 1/32:
            if grace_note_duration > Fraction(1, 32):
                grace_note_duration = Fraction(1, 32)

            if grace_note_duration > adorned_note.note.duration * Fraction(
                    1, 2):

                grace_note_duration = adorned_note.note.duration * Fraction(
                    1, 2)
            """

            # Check if the current note has a duration longer than 1/64
            # if so check if the duration is greater than 1/32, if so
            # set the duration to be 1/32 if not set it to 1/64
            # if the unadorned note is shorter than 1/64 in duration
            # do no apply a grace note.
            if adorned_note.adornment.grace_note.on_beat:
                if unadorned_note.duration >= Fraction(1, 16):
                    grace_note_duration = Fraction(1, 32)

                else:
                    grace_note_duration = Fraction(float(unadorned_note.duration)*0.5)
            else:
                grace_note_duration = Fraction(1,32)

            grace_note = GraceNote(
                grace_note_fret, grace_note_duration,
                adorned_note.adornment.grace_note.dynamic,
                adorned_note.adornment.grace_note.dead_note,
                adorned_note.adornment.grace_note.on_beat,
                grace_note_transision)

            if grace_note not in grace_notes:
                grace_notes.append(grace_note)
            """
            grace_notes.append(
                GraceNote(grace_note_fret,
                          adorned_note.adornment.grace_note.duration,
                          adorned_note.adornment.grace_note.dynamic,
                          adorned_note.adornment.grace_note.dead_note,
                          adorned_note.adornment.grace_note.on_beat,
                          adorned_note.adornment.grace_note.transition))
            """
        else:
            if None not in grace_notes:
                grace_notes.append(None)

        # Ghost notes, if the unadorned note is the same, or shorter duration
        # than the adorned note:
        if adorned_note.adornment.ghost_note:
            if unadorned_note.duration <= adorned_note.note.duration:
                assert isinstance(adorned_note.adornment.ghost_note, bool)
                ghost_notes = adorned_note.adornment.ghost_note

        if adorned_note.adornment.fretting.modification.let_ring:
            fretting_modifications_let_ring = True

    out = namedtuple('PossibleAdornments', [
        'dynamics', 'plucking_accents', 'fretting_accents',
        'plucking_techniques', 'plucking_modifications_ah',
        'plucking_modifications_palm_mute', 'fretting_techniques',
        'fretting_modifications_type', 'fretting_modifications_let_ring',
        'fretting_modulations_bend', 'fretting_modulations_trill',
        'fretting_modulations_vib', 'fretting_modulations_slide',
        'grace_notes', 'ghost_notes'
    ])
    output = out(dynamics, plucking_accents, fretting_accents,
                 plucking_techniques, plucking_modifications_ah,
                 plucking_modifications_palm_mute, fretting_techniques,
                 fretting_modifications_type, fretting_modifications_let_ring,
                 fretting_modulations_bend, fretting_modulations_trill,
                 fretting_modulations_vib, fretting_modulations_slide,
                 grace_notes, ghost_notes)

    del (dynamics, plucking_accents, fretting_accents, plucking_techniques,
         plucking_modifications_ah, plucking_modifications_palm_mute,
         fretting_techniques, fretting_modifications_type,
         fretting_modifications_let_ring, fretting_modulations_bend,
         fretting_modulations_trill, fretting_modulations_vib,
         fretting_modulations_slide, grace_notes, ghost_notes)

    return output


def possible_natural_harmonic_pitches(string_tuning):

    possible_natural_harmonic_notes = {}
    for string in list(string_tuning.keys()):
        for fret in list(utilities.fret_2_harmonic_interval.keys()):

            if utilities.fret_2_harmonic_interval[fret] == 'none':
                continue

            pitch = string_tuning[string] + utilities.fret_2_harmonic_interval[fret]

            natura_harmonic_pos = namedtuple("NaturalHarmonicPos",
                                             ["string", 'fret'])

            # check if the pitch is in the possible notes:
            if not possible_natural_harmonic_notes.get(pitch, False):
                possible_natural_harmonic_notes[pitch] = [
                    natura_harmonic_pos(string, fret)
                ]
            else:
                possible_natural_harmonic_notes[pitch].append(
                    natura_harmonic_pos(string, fret))
    return possible_natural_harmonic_notes


def possible_artificial_harmonic_pitches(string_tuning):

    # the types of artificial harmonic:
    # [octave, semitone interval]
    artificial_harmonics = {
        1: [1, 0],
        2: [1, 8],
        3: [2, 0],
        4: [2, 4],
        5: [2, 8],
        6: [2, 10],
        7: [3, 0]
    }

    possible_artificial_harmonics = {}
    for string in list(string_tuning.keys()):
        for fret in range(1, 25):
            fundamental = string_tuning[string] + fret

            for ah in list(artificial_harmonics.keys()):
                octave = artificial_harmonics[ah][0]
                interval = artificial_harmonics[ah][1]
                pitch = fundamental + octave * 12 + interval
                ah_possition = namedtuple('AHPos', ['string', 'fret', 'ah'])

                if not possible_artificial_harmonics.get(pitch, False):
                    possible_artificial_harmonics[pitch] = [
                        ah_possition(string, fret, artificial_harmonics[ah])
                    ]
                else:
                    possible_artificial_harmonics[pitch].append(
                        ah_possition(string, fret, artificial_harmonics[ah]))

    return possible_artificial_harmonics
