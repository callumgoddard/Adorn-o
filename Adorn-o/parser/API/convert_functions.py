import guitarpro

# Information on how to make blank guitar pro data structures:
# model tests:
# Make a blank song, track, measure, voice, beat then note
# and print the note
# test_song = guitarpro.models.Song()
# track = guitarpro.models.Track(test_song)
# measure = guitarpro.models.Measure(track)
# voice = guitarpro.models.Voice(measure)
# beat = guitarpro.models.Beat(voice)

# Arguments: guitarpro.models.Note(beat, value=0, velocity=95,
#                                       string=0, effect=NOTHING,
#                                       durationPercent=1.0,
#                                       swapAccidentals=False,
#                                       type=<NoteType.rest: 0>)
# guitarpro.models.Note(beat)

# type =
#    rest = 0
#    normal = 1
#    tie = 2
#    dead = 3
# print guitarpro.models.NoteType(1)


# Set a note
def make_gp5_note(note_data,
                  song=None,
                  track=None,
                  measure=None,
                  voice=None,
                  beat=None):
    if song is None:
        song = guitarpro.models.Song()
    if track is None:
        track = guitarpro.models.Track(song)
    if measure is None:
        measure = guitarpro.models.Measure(track)
    if voice is None:
        voice = guitarpro.models.Voice(measure)
    if beat is None:
        beat = guitarpro.models.Beat(voice)

    # make a note
    # read all the note data from note_data... and make the note.
    # Need to do tests for what is in the note data

    gp5_note = guitarpro.models.Note(beat)

    return gp5_note


def make_gp5_song(song):
    song.meta_data.title
    gp5_song = guitarpro.models.Song(
        versionTuple=(5, 1, 0),
        clipboard=None,
        title=str(song.meta_data.title),
        tempoName='',
        tempo=120,
        key='',
        measureHeaders=[],
    )
    print(gp5_song)
    return


def gp5_key_sig(key_sig):
    '''
    Convert key signature string to a GP5 KeySignature
    '''
    return guitarpro.models.KeySignature({
        "FMajorFlat": (-8, 0),
        'CMajorFlat': (-7, 0),
        'GMajorFlat': (-6, 0),
        'DMajorFlat': (-5, 0),
        'AMajorFlat': (-4, 0),
        'EMajorFlat': (-3, 0),
        'BMajorFlat': (-2, 0),
        'FMajor': (-1, 0),
        'CMajor': (0, 0),
        'GMajor': (1, 0),
        'DMajor': (2, 0),
        'AMajor': (3, 0),
        'EMajor': (4, 0),
        'BMajor': (5, 0),
        'FMajorSharp': (6, 0),
        'CMajorSharp': (7, 0),
        'GMajorSharp': (8, 0),
        'DMinorFlat': (-8, 1),
        'AMinorFlat': (-7, 1),
        'EMinorFlat': (-6, 1),
        'BMinorFlat': (-5, 1),
        'FMinor': (-4, 1),
        'CMinor': (-3, 1),
        'GMinor': (-2, 1),
        'DMinor': (-1, 1),
        'AMinor': (0, 1),
        'EMinor': (1, 1),
        'BMinor': (2, 1),
        'FMinorSharp': (3, 1),
        'CMinorSharp': (4, 1),
        'GMinorSharp': (5, 1),
        'DMinorSharp': (6, 1),
        'AMinorSharp': (7, 1),
        'EMinorSharp': (8, 1),
    }.get(key_sig))


def gp5_tuplet(tuplet):
    '''
    Convert tuplet datatype to GP5 data type
    '''
    return guitarpro.models.Tuplet(tuplet.number_of_notes, tuplet.equal_to)


def gp5_tempo(tempo):
    '''
    Convert tempo value datatype to GP5 data type
    '''
    return guitarpro.models.Tempo(tempo)


def gp5_duration(notated_duration):
    '''
    Convert notated_duration datatype to GP5 data type
    '''
    return guitarpro.models.Duration(notated_duration.value,
                                     notated_duration.isDotted,
                                     notated_duration.isDoubleDotted,
                                     gp5_tuplet(notated_duration.tuplet))


def gp5_time_signature():
    return
