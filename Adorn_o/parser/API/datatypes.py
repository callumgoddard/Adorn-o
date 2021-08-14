from collections import namedtuple

Song = namedtuple('Song', ['meta_data', 'measures'])

SongMetaData = namedtuple('SongMetaData',
                          ['artist', 'title', 'bpm', 'key', 'number_of_measures'])

Measure = namedtuple('Measure', ['meta_data', 'start_time', 'notes'])

MeasureMetaData = namedtuple('MeasureMetaData', [
    'title', 'number', 'key_signature', 'time_signature', 'tempo',
    'triplet_feel', 'monophonic', 'only_tied_notes', 'only_rests'
])

Rest = namedtuple(
    'Rest', ['note_number', 'start_time', 'duration', 'notated_duration'])


Note = namedtuple('Note', [
    'note_number', 'pitch', 'fret_number', 'string_number', 'string_tuning',
    'start_time', 'duration', 'notated_duration', 'dynamic'
])

NotatedDuration = namedtuple('NotatedDuration',
                             ['value', 'isDotted', 'isDoubleDotted', 'tuplet'])

Tuplet = namedtuple('Tuplet', ['number_of_notes', 'equal_to'])

Dynamic = namedtuple('Dynamic', ['value', 'cres_dim'])

AdornedNote = namedtuple('AdornedNote', ['note', 'adornment'])

Adornment = namedtuple('Adornment',
                       ['plucking', 'fretting', 'grace_note', 'ghost_note'])

PluckingAdornment = namedtuple('PluckingAdornment',
                               ['technique', 'modification', 'accent'])

PluckingModification = namedtuple('PluckingModification',
                                  ['palm_mute', 'artificial_harmonic'])

ArtificialHarmonic = namedtuple('ArtificialHarmonic', ['octave', 'pitch'])

FrettingAdornment = namedtuple(
    'FrettingAdornment', ['technique', 'modification', 'accent', 'modulation'])

FrettingModification = namedtuple('FrettingModification',
                                  ['type', 'let_ring'])

Modulation = namedtuple('Modulation', ['bend', 'vibrato', 'trill', 'slide'])

Bend = namedtuple('Bend', ['type', 'value', 'points'])
BendPoint = namedtuple('BendPoint', ['position', 'value', 'vibrato'])

#Vibrato = namedtuple('Vibrato', ['value'])

Trill = namedtuple('Trill', ['fret', 'notated_duration'])

Slide = namedtuple('Slide', ['into', 'outto'])

MIDINote = namedtuple('MIDINote', ['pitch', 'time', 'duration', 'volume'])

BasicNote = namedtuple('BasicNote', ['pitch', 'time', 'duration', 'volume'])

GraceNote = namedtuple(
    'GraceNote',
    ['fret', 'duration', 'dynamic', 'dead_note', 'on_beat', 'transition'])
