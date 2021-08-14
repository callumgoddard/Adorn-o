'''
API functions to update data within the API
'''
#from __future__ import division, print_function, absolute_import

# Local Application Imports
from . import datatypes


def update_rest(rest, **field_values_pairs):
    assert isinstance(
        rest, datatypes.Rest), ("%s is not a Rest datatype" % (type(rest)))
    note_number = field_values_pairs.get("note_number", rest.note_number)
    start_time = field_values_pairs.get("start_time", rest.start_time)
    duration = field_values_pairs.get("duration", rest.duration)
    notated_duration = field_values_pairs.get("notated_duration",
                                              rest.notated_duration)

    assert isinstance(notated_duration, datatypes.NotatedDuration)
    return rest._replace(
        note_number=note_number,
        start_time=start_time,
        duration=duration,
        notated_duration=notated_duration)


def update_note(note, **field_values_pairs):
    '''
    Update the note fields, with the values specified by field_value_pairs
    '''

    # Check that a note is passe into the function
    assert isinstance(
        note, datatypes.Note), ("%s is not a Note datatype" % (type(note)))

    note_number = field_values_pairs.get("note_number", note.note_number)
    pitch = field_values_pairs.get("pitch", note.pitch)
    fret_number = field_values_pairs.get("fret_number", note.fret_number)
    string_number = field_values_pairs.get("string_number", note.string_number)
    string_tuning = field_values_pairs.get("string_tuning", note.string_tuning)
    start_time = field_values_pairs.get("start_time", note.start_time)
    duration = field_values_pairs.get("duration", note.duration)
    notated_duration = field_values_pairs.get("notated_duration",
                                              note.notated_duration)
    dynamic = field_values_pairs.get("dynamic", note.dynamic)

    return note._replace(
        note_number=note_number,
        pitch=pitch,
        fret_number=fret_number,
        string_number=string_number,
        string_tuning=string_tuning,
        start_time=start_time,
        duration=duration,
        notated_duration=notated_duration,
        dynamic=dynamic)


def update_adornment(adornment, **field_values_pairs):
    '''
    Update the adornment fields, with the values specified by field_value_pairs
    '''
    assert isinstance(adornment, datatypes.Adornment), (
        "%s is not an Adornment datatype" % (type(adornment)))

    fretting = field_values_pairs.get("fretting", adornment.fretting)
    plucking = field_values_pairs.get("plucking", adornment.plucking)
    grace_note = field_values_pairs.get("grace_note", adornment.grace_note)
    ghost_note = field_values_pairs.get("ghost_note", adornment.ghost_note)

    return adornment._replace(fretting=fretting, plucking=plucking, grace_note=grace_note, ghost_note=ghost_note)


def update_plucking_adornment(plucking_adornment, **field_values_pairs):
    '''
    Update the plucking_adornment fields, with the values
    specified by field_value_pairs
    '''
    assert isinstance(plucking_adornment, datatypes.PluckingAdornment), (
        "%s is not a PluckingAdornment datatype" % (type(plucking_adornment)))

    technique = field_values_pairs.get("technique",
                                       plucking_adornment.technique)
    modification = field_values_pairs.get("modification",
                                          plucking_adornment.modification)
    accent = field_values_pairs.get("accent", plucking_adornment.accent)

    return plucking_adornment._replace(
        technique=technique, modification=modification, accent=accent)


def update_fretting_adornment(fretting_adornment, **field_values_pairs):
    '''
    Update the plucking_adornment fields, with the values
    specified by field_value_pairs
    '''
    assert isinstance(fretting_adornment, datatypes.FrettingAdornment), (
        "%s is not a FrettingAdornment datatype" % (type(fretting_adornment)))

    technique = field_values_pairs.get("technique",
                                       fretting_adornment.technique)
    modification = field_values_pairs.get("modification",
                                          fretting_adornment.modification)
    accent = field_values_pairs.get("accent", fretting_adornment.accent)
    modulation = field_values_pairs.get("modulation",
                                        fretting_adornment.modulation)

    return fretting_adornment._replace(
        technique=technique,
        modification=modification,
        accent=accent,
        modulation=modulation)


def update_modulation(modulation, **field_values_pairs):
    '''
    Update the modulation fields, with the values
    specified by field_value_pairs
    '''
    assert isinstance(modulation, datatypes.Modulation), (
        "%s is not a FrettingAdornment datatype" % (type(modulation)))

    bend = field_values_pairs.get("bend", modulation.bend)
    vibrato = field_values_pairs.get("vibrato", modulation.vibrato)
    trill = field_values_pairs.get("trill", modulation.trill)
    slide = field_values_pairs.get("slide", modulation.slide)

    return modulation._replace(
        bend=bend, vibrato=vibrato, trill=trill, slide=slide)


def update_modulation_in_fretting_adornment(modulation, fretting_adornment,
                                            **field_values_pairs):
    '''
    Update the modulation fields, with the values
    specified by field_value_pairs, and then update
    the fretting adornment that the modulation is part of.
    '''
    assert isinstance(modulation, datatypes.Modulation), (
        "%s is not a Modulation datatype" % (type(modulation)))

    bend = field_values_pairs.get("bend", modulation.bend)
    vibrato = field_values_pairs.get("vibrato", modulation.vibrato)
    trill = field_values_pairs.get("trill", modulation.trill)
    slide = field_values_pairs.get("slide", modulation.slide)

    modulation = update_modulation(
        modulation, bend=bend, vibrato=vibrato, trill=trill, slide=slide)
    return update_fretting_adornment(fretting_adornment, modulation=modulation)


def update_plucking_in_adornment(plucking, adornment, **field_values_pairs):
    '''
    Update the plucking fields, with the values
    specified by field_value_pairs, and then update
    the adornment that the plucking is part of.
    '''

    assert isinstance(plucking, datatypes.PluckingAdornment), (
        "%s is not a PluckingAdornment datatype" % (type(plucking)))

    technique = field_values_pairs.get("technique", plucking.technique)
    modification = field_values_pairs.get("modification",
                                          plucking.modification)
    accent = field_values_pairs.get("accent", plucking.accent)

    plucking = update_plucking_adornment(
        plucking,
        technique=technique,
        modification=modification,
        accent=accent)

    return update_adornment(adornment, plucking=plucking)


def update_fretting_in_adornment(fretting, adornment, **field_values_pairs):
    '''
    Update the fretting fields, with the values
    specified by field_value_pairs, and then update
    the adornment that the fretting is part of.
    '''
    assert isinstance(fretting, datatypes.FrettingAdornment), (
        "%s is not a FrettingAdornment datatype" % (type(fretting)))

    technique = field_values_pairs.get("technique", fretting.technique)
    modification = field_values_pairs.get("modification",
                                          fretting.modification)
    accent = field_values_pairs.get("accent", fretting.accent)
    modulation = field_values_pairs.get("modulation", fretting.modulation)

    fretting = update_fretting_adornment(
        fretting,
        technique=technique,
        modification=modification,
        accent=accent,
        modulation=modulation)

    return update_adornment(adornment, fretting=fretting)


def update_adornment_in_adorned_note(adornment, adorned_note,
                                     **field_values_pairs):
    '''
    Update the adornment fields, with the values
    specified by field_value_pairs,
    and then update the adorned_note with
    the newly updated adornment.
    '''
    assert isinstance(adornment, datatypes.Adornment), (
        "%s is not an Adornment datatype" % (type(adornment)))

    plucking = field_values_pairs.get("plucking", adornment.plucking)
    fretting = field_values_pairs.get("fretting", adornment.fretting)
    grace_note = field_values_pairs.get("grace_note", adornment.grace_note)
    ghost_note = field_values_pairs.get("ghost_note", adornment.ghost_note)

    """
    if fretting:
        adornment = update_adornment(adorned_note.adornment, fretting=fretting)
    if plucking:
        adornment = update_adornment(adorned_note.adornment, plucking=plucking)
    if fretting and plucking:
    """
    adornment = update_adornment(adorned_note.adornment, plucking=plucking, fretting=fretting, grace_note=grace_note,ghost_note=ghost_note )


    return update_adorned_note(adorned_note,adornment=adornment)


def update_note_in_adorned_note(note, adorned_note, **field_values_pairs):
    '''
    Update the note fields, with the values specified by field_value_pairs,
    and then update the adorned_note with the newly updated note.
    '''

    # Check that a note is passe into the function
    assert isinstance(
        note, datatypes.Note), ("%s is not a Note datatype" % (type(note)))

    note_number = field_values_pairs.get("note_number", note.note_number)
    pitch = field_values_pairs.get("pitch", note.pitch)
    fret_number = field_values_pairs.get("fret_number", note.fret_number)
    string_number = field_values_pairs.get("string_number", note.string_number)
    string_tuning = field_values_pairs.get("string_tuning", note.string_tuning)
    start_time = field_values_pairs.get("start_time", note.start_time)
    duration = field_values_pairs.get("duration", note.duration)
    notated_duration = field_values_pairs.get("notated_duration",
                                              note.notated_duration)
    dynamic = field_values_pairs.get("dynamic", note.dynamic)

    note = note._replace(
        note_number=note_number,
        pitch=pitch,
        fret_number=fret_number,
        string_number=string_number,
        string_tuning=string_tuning,
        start_time=start_time,
        duration=duration,
        notated_duration=notated_duration,
        dynamic=dynamic)
    return update_adorned_note(adorned_note, note=note)


def update_adorned_note(adorned_note, **values_to_update):
    '''
    Update the adorned_note fields, with the values
    specified by field_value_pairs
    '''

    assert isinstance(adorned_note, datatypes.AdornedNote), (
        "%s is not an AdornedNote datatype" % (type(adorned_note, )))

    note = values_to_update.get("note", adorned_note.note)
    adornment = values_to_update.get("adornment", adorned_note.adornment)

    return adorned_note._replace(note=note, adornment=adornment)


def update_note_in_measure(adorned_note, new_adorned_note, measure):
    '''
    Replace the note in measure.notes with the new_note
    '''
    assert isinstance(
        measure,
        datatypes.Measure), ("%s is not a Measure datatype" % (type(measure)))
    assert (isinstance(adorned_note, datatypes.Rest)
            or isinstance(adorned_note, datatypes.AdornedNote)), (
                "%s is not a Note or Rest datatype" % (type(new_adorned_note)))
    assert (isinstance(new_adorned_note, datatypes.Rest)
            or isinstance(new_adorned_note, datatypes.AdornedNote)), (
                "%s is not a Note or Rest datatype" % (type(new_adorned_note)))
    assert ((isinstance(adorned_note, datatypes.Rest)
             and isinstance(new_adorned_note, datatypes.Rest))
            or (isinstance(adorned_note, datatypes.AdornedNote)
                and isinstance(new_adorned_note, datatypes.AdornedNote))), (
                    "The adorned note and new_adorned_note data types do not match")

    # find the note in the measure.notes
    note_index = measure.notes.index(adorned_note)
    notes = measure.notes
    # replace it with the new_note
    notes[note_index] = new_adorned_note

    # return the updated measure
    return measure._replace(notes=notes)


def update_measure_in_song(measure, new_measure, song):
    '''
    Replace the measure in song.measures with the new_measure
    '''
    assert isinstance(
        measure,
        datatypes.Measure), ("%s is not a Measure datatype" % (type(measure)))
    assert isinstance(new_measure, datatypes.Measure), (
        "%s is not a Measure datatype" % (type(new_measure)))
    assert isinstance(
        song, datatypes.Song), ("%s is not a Song datatype" % (type(song)))

    new_measure_index = song.measures.index(measure)
    song.measures[new_measure_index] = new_measure

    return song


def update_measure_meta_data(measure, **new_meta_data):
    '''
    Update the meta_data information in a measure with new_meta_data
    '''
    assert isinstance(
        measure,
        datatypes.Measure), ("%s is not a Measure datatype" % (type(measure)))

    # Note: title, number, key_signature, time_signature, tempo
    # should not be able to be changed. Only triplet feel and monophonic.
    triplet_feel = new_meta_data.get("triplet_feel",
                                     measure.meta_data.triplet_feel)
    monophonic = new_meta_data.get("monophonic", measure.meta_data.monophonic)

    updated_meta_data = measure.meta_data._replace(
        triplet_feel=triplet_feel, monophonic=monophonic)
    return measure._replace(meta_data=updated_meta_data)


def add_measure_to_song(new_measure, song):
    '''
    Add the new_measure to song.measures
    '''
    assert isinstance(new_measure, datatypes.Measure), (
        "%s is not a Measure datatype" % (type(new_measure)))
    assert isinstance(
        song.datatypes.Song), ("%s is not a Song datatype" % (type(song)))

    song.measure.append(new_measure)

    return song
