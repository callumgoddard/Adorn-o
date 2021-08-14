'''
Functions to read and gather data from the API data structures
'''

# Standard library imports

# 3rd party imports

# Local application imports
from . import datatypes
from .. import utilities


def read_hammer_on(adorned_note):

    return


def read_pull_off(adorned_note):

    return


def read_finger_style():

    return


def read_tied_note():
    return


def read_plucking_technique(adornment):
    '''
    Read plucking technique from adornment
    '''
    return adornment.plucking.technique


def read_plucking_modification(adornment):
    '''
    Read plucking modification from adornment
    '''
    return adornment.plucking.modification


def read_plucking_accent(adornment):
    '''
    Read plucking accent from adornment
    '''
    return adornment.plucking.accent


def read_all_adorned_notes_in_a_song(song):
    '''
    Reads all the notes in the song and returns:
    [
    [<list of first measure's notes>],
    [<list of second measure's notes>],
    ... ,
    [<list of nth measure's notes>],
    ]
    '''
    return [m.notes for m in song.measures]


def read_all_note_durations(song_or_measure, tied_notes='combine'):
    '''
    gets all the durations from all the notes in the song_or_measure
    '''
    basic_data = read_basic_note_data(song_or_measure, tied_notes)

    note_durations = [d[2] for d in basic_data]

    return note_durations


def read_all_note_dynamics(song_or_measure, tied_notes='combine'):
    '''
    gets all the durations from all the notes in the song_or_measure
    '''
    basic_data = read_basic_note_data(song_or_measure, tied_notes)

    note_dynamics = [d[3] for d in basic_data]

    return note_dynamics


def read_all_note_dynamics_as_velocities(song_or_measure,
                                         tied_notes='combine'):
    '''
    gets all the durations from all the notes in the song_or_measure
    '''
    basic_data = read_basic_note_data(song_or_measure, tied_notes)

    note_dynamics = [d[3][0] for d in basic_data]
    return [utilities.dynamics_inv.get(v) for v in note_dynamics]


def read_basic_note_data(api_data, tied_notes='combine'):
    '''
    Read and then return a list of basic notes
    which have a: pitch, start_time, duration, and volume (in midi volume)
    '''

    assert (isinstance(api_data, datatypes.Song)
            or isinstance(api_data, datatypes.Measure)), (
                "Input isn't a Song or Measure datatype")

    note_list = []
    # check to see if a measure or song is passed
    if isinstance(api_data, datatypes.Song):
        for measure in api_data.measures:
            for note in measure.notes:
                if note_list is []:
                    if isinstance(note, datatypes.AdornedNote):
                        pitch = note.note.pitch
                        time = note.note.start_time
                        duration = note.note.duration
                        volume = note.note.dynamic

                        note_list += [[pitch, time, duration, volume]]
                else:
                    if isinstance(note, datatypes.AdornedNote):
                        if note.adornment.plucking.technique is "tied":
                            for prev_note in note_list:
                                if tied_notes is 'combine':
                                    if prev_note[0] == note.note.pitch:

                                        if (prev_note[1] + prev_note[2] ==
                                                note.note.start_time):

                                            # found the notes that need to be tied
                                            # add the durations on:
                                            tied_duration = (
                                                prev_note[2] +
                                                note.note.duration)

                                            # find where to replace the
                                            # previous note:
                                            prev_note_index = note_list.index(
                                                prev_note)

                                            # update the duration value:
                                            prev_note[2] = tied_duration

                                            # replace the note in previous
                                            note_list[prev_note_index] = (
                                                prev_note)

                                            break
                                elif tied_notes is 'ignore':
                                    break

                                elif tied_notes is 'keep':
                                    pitch = note.note.pitch
                                    time = note.note.start_time
                                    duration = note.note.duration
                                    volume = note.note.dynamic

                                    note_list += [[
                                        pitch, time, duration, volume
                                    ]]

                        else:
                            # note is not tied so add it separately:
                            pitch = note.note.pitch
                            time = note.note.start_time
                            duration = note.note.duration
                            volume = note.note.dynamic

                            note_list += [[pitch, time, duration, volume]]
    # check to see if a measure or song is passed
    elif isinstance(api_data, datatypes.Measure):
        measure = api_data
        for note in measure.notes:
            if note_list is []:
                if isinstance(note, datatypes.AdornedNote):
                    pitch = note.note.pitch
                    time = note.note.start_time
                    duration = note.note.duration
                    volume = note.note.dynamic

                    note_list += [[pitch, time, duration, volume]]
            else:
                if isinstance(note, datatypes.AdornedNote):
                    if note.adornment.plucking.technique is "tied":
                        for prev_note in note_list:
                            if tied_notes is 'combine':
                                if prev_note[0] == note.note.pitch:

                                    if (prev_note[1] + prev_note[2] ==
                                            note.note.start_time):

                                        # found the notes that need to be tied
                                        # add the durations on:
                                        tied_duration = (
                                            prev_note[2] +
                                            note.note.duration)

                                        # find where to replace the
                                        # previous note:
                                        prev_note_index = note_list.index(
                                            prev_note)

                                        # update the duration value:
                                        prev_note[2] = tied_duration

                                        # replace the note in previous
                                        note_list[prev_note_index] = (
                                            prev_note)

                                        break
                            elif tied_notes is 'ignore':
                                break

                            elif tied_notes is 'keep':
                                pitch = note.note.pitch
                                time = note.note.start_time
                                duration = note.note.duration
                                volume = note.note.dynamic

                                note_list += [[
                                    pitch, time, duration, volume
                                ]]

                    else:
                        # note is not tied so add it separately:
                        pitch = note.note.pitch
                        time = note.note.start_time
                        duration = note.note.duration
                        volume = note.note.dynamic

                        note_list += [[pitch, time, duration, volume]]
    return note_list
