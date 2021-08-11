"""
Functions to convert the API datatypes into dicts, and vice versa
for use with JSON read/writing
"""
import guitarpro
from fractions import Fraction
from decimal import Decimal
from collections import OrderedDict

from parser.API import datatypes


def tracks_to_dict(api_songs):

    tracks = []
    for api_song in api_songs:

        tracks.append(Song_to_dict(api_song))
    return {'tracks': tracks}


def dict_to_tracks(track_dict):
    tracks = []
    for song_dict in track_dict['tracks']:
        tracks.append(dict_to_Song(song_dict))

    return tracks


def Song_to_dict(api_song):
    """ coverts Song data type into a dict
    """

    assert isinstance(api_song, datatypes.Song)

    measure_dicts = []
    for measure in api_song.measures:
        measure_dicts.append(Measure_to_dict(measure))

    return {
        'song':
        OrderedDict([('meta_data', SongMetaData_to_dict(api_song.meta_data)),
                     ('measures', measure_dicts)])
    }


def dict_to_Song(song_dict):
    """ convert a song_dict into Song namedtuple
    """
    measures = []
    for measure in song_dict['song']['measures']:
        measures.append(dict_to_Measure(measure))
    return datatypes.Song(
        dict_to_SongMetaData(song_dict['song']['meta_data']), measures)


def SongMetaData_to_dict(meta_data):
    """ convert the song meta data namedtuple into a dict
    """

    assert isinstance(meta_data, datatypes.SongMetaData)

    return OrderedDict([('artist', meta_data.artist), ('title',
                                                       meta_data.title),
                        ('bpm', meta_data.bpm), ('key', meta_data.key),
                        ('number_of_measures', meta_data.number_of_measures)])


def dict_to_SongMetaData(meta_data_dict):
    """ convert the song dict to Song namedtuple
    """

    return datatypes.SongMetaData(
        meta_data_dict['artist'],
        meta_data_dict['title'], meta_data_dict['bpm'],
        str(meta_data_dict['key']), meta_data_dict['number_of_measures'])


def Measure_to_dict(measure):
    """ convert Measure namedtuple to dict
    """

    assert isinstance(measure, datatypes.Measure)

    notes = []
    for note in measure.notes:
        if isinstance(note, datatypes.AdornedNote):
            notes.append(AdornedNote_to_dict(note))
        elif isinstance(note, datatypes.Rest):
            notes.append(Rest_to_dict(note))

    return OrderedDict([('meta_data', MeasureMetaData_to_dict(
        measure.meta_data)), ('start_time', fraction_to_dict(measure.start_time)),
                        ('notes', notes)])


def dict_to_Measure(measure_dict):
    """ convert a dict to Measure namedtuple
    """

    notes = []
    for note in measure_dict['notes']:
        if u'rest' in note.keys():
            notes.append(dict_to_Rest(note))
        elif u'adorned_note' in note.keys():
            notes.append(dict_to_AdornedNote(note))

    return datatypes.Measure(
        dict_to_MeasureMetaData(measure_dict['meta_data']),
        dict_to_fraction(measure_dict['start_time']), notes)


def MeasureMetaData_to_dict(meta_data):
    """ Convert the measure meta data into a dict
    """

    assert isinstance(meta_data, datatypes.MeasureMetaData)
    return OrderedDict(
        [('title', meta_data.title), ('number', meta_data.number),
         ('key_signature',
          meta_data.key_signature), ('time_signature',
                                     meta_data.time_signature),
         ('tempo',
          meta_data.tempo), ('triplet_feel',
                             meta_data.triplet_feel), ('monophonic',
                                                       meta_data.monophonic),
         ('only_tied_notes',
          meta_data.only_tied_notes), ('only_rests', meta_data.only_rests)])


def dict_to_MeasureMetaData(meta_data_dict):
    """convert a dict to MeasureMetaData
    """
    return datatypes.MeasureMetaData(
        meta_data_dict['title'], meta_data_dict['number'],
        str(meta_data_dict['key_signature']),
        str(meta_data_dict['time_signature']), meta_data_dict['tempo'],
        meta_data_dict['triplet_feel'], meta_data_dict['monophonic'],
        meta_data_dict['only_tied_notes'], meta_data_dict['only_rests'])


def NotatedDuration_to_dict(notated_duration):
    """ convert the notated duration namedtuple to a dict
    """
    assert isinstance(notated_duration, datatypes.NotatedDuration)

    return OrderedDict([('value', fraction_to_dict(
        notated_duration.value)), ('isDotted', notated_duration.isDotted),
                        ('isDoubleDotted', notated_duration.isDoubleDotted),
                        ('tuplet', Tuplet_to_dict(notated_duration.tuplet))])


def dict_to_NotatedDuration(notated_duration_dict):

    notated_duration_dict['value']

    return datatypes.NotatedDuration(
        dict_to_fraction(notated_duration_dict['value']),
        notated_duration_dict['isDotted'],
        notated_duration_dict['isDoubleDotted'],
        dict_to_Tuplet(notated_duration_dict['tuplet']))


def Tuplet_to_dict(tuplet):
    """ convert tuplet namedtuple to a dict
    """

    assert isinstance(tuplet, datatypes.Tuplet)

    return OrderedDict([('number_of_notes', tuplet.number_of_notes),
                        ('equal_to', tuplet.equal_to)])


def dict_to_Tuplet(tuplet_dict):
    return datatypes.Tuplet(tuplet_dict['number_of_notes'],
                            tuplet_dict['equal_to'])


def Rest_to_dict(rest):
    """ convert Rest datatype into a dict
    """
    assert isinstance(rest, datatypes.Rest)

    return {
        'rest':
        OrderedDict(
            [('note_number', rest.note_number), ('start_time',
                                                 fraction_to_dict(rest.start_time)),
             ('duration', fraction_to_dict(rest.duration)), ('notated_duration',
                                                  NotatedDuration_to_dict(
                                                      rest.notated_duration))])
    }


def dict_to_Rest(rest_dict):

    return datatypes.Rest(
        rest_dict['rest']['note_number'],
        dict_to_fraction(rest_dict['rest']['start_time']),
        dict_to_fraction(rest_dict['rest']['duration']),
        dict_to_NotatedDuration(rest_dict['rest']['notated_duration']))


def AdornedNote_to_dict(note):

    assert isinstance(note, datatypes.AdornedNote)
    return {
        'adorned_note':
        OrderedDict([('note', Note_to_dict(note.note)),
                     ('adornment', Adorment_to_dict(note.adornment))])
    }


def dict_to_AdornedNote(adorned_note_dict):

    adorned_note_dict['adorned_note']

    return datatypes.AdornedNote(
        dict_to_Note(adorned_note_dict['adorned_note']['note']),
        dict_to_Adornment(adorned_note_dict['adorned_note']['adornment']))


def Note_to_dict(note):

    return OrderedDict(
        [('note_number', note.note_number), ('pitch', note.pitch),
         ('fret_number',
          note.fret_number), ('string_number',
                              note.string_number), ('string_tuning',
                                                    note.string_tuning),
         ('start_time', fraction_to_dict(note.start_time)), ('duration',
                                                  fraction_to_dict(note.duration)),
         ('notated_duration', NotatedDuration_to_dict(
             note.notated_duration)), ('dynamic',
                                       Dynamic_to_dict(note.dynamic))])


def dict_to_Note(note):

    return datatypes.Note(note['note_number'], note['pitch'],
                          note['fret_number'], note['string_number'],
                          dict_to_StringTuning(note['string_tuning']),
                          dict_to_fraction(note['start_time']),
                          dict_to_fraction(note['duration']),
                          dict_to_NotatedDuration(note['notated_duration']),
                          dict_to_Dynamic(note['dynamic']))


def dict_to_StringTuning(string_tuning_dict):

    string_tuning = {}
    for string in range(1, 7):
        if string_tuning_dict.get(str(string), False):
            string_tuning[string] = string_tuning_dict[str(string)]
        elif string_tuning_dict.get(string, False):
            string_tuning[string] = string_tuning_dict[string]

    return string_tuning


def Dynamic_to_dict(dynamic):
    """ convert Dynamic namedtuple to dict
    """
    assert isinstance(dynamic, datatypes.Dynamic)
    return OrderedDict([('value', dynamic.value), ('cres_dim',
                                                   dynamic.cres_dim)])


def dict_to_Dynamic(dynamic_dict):
    return datatypes.Dynamic(dynamic_dict['value'], dynamic_dict['cres_dim'])


def Adorment_to_dict(adornment):

    return OrderedDict([('plucking',
                         PluckingAdornment_to_dict(adornment.plucking)),
                        ('fretting',
                         FrettingAdornment_to_dict(adornment.fretting)),
                        ('grace_note', GraceNote_to_dict(
                            adornment.grace_note)), ('ghost_note',
                                                     adornment.ghost_note)])


def dict_to_Adornment(adornment_dict):

    return datatypes.Adornment(
        dict_to_PluckingAdornment(adornment_dict['plucking']),
        dict_to_FrettingAdornment(adornment_dict['fretting']),
        dict_to_GraceNote(adornment_dict['grace_note']),
        adornment_dict['ghost_note'])


def PluckingAdornment_to_dict(plucking):
    """ convert PluckingAdornment namedtuple to dict
    """
    assert isinstance(plucking, datatypes.PluckingAdornment)
    return OrderedDict([('technique', plucking.technique),
                        ('modification',
                         PluckingModification_to_dict(plucking.modification)),
                        ('accent', plucking.accent)])


def dict_to_PluckingAdornment(plucking_dict):
    plucking_technique = str(plucking_dict['technique'])
    if plucking_technique == 'None':
        plucking_technique = None

    return datatypes.PluckingAdornment(
        plucking_technique,
        dict_to_PluckingModification(plucking_dict['modification']),
        plucking_dict['accent'])


def PluckingModification_to_dict(plucking_mod):
    """ convert PluckingModification namedtuple to dict
    """
    assert isinstance(plucking_mod, datatypes.PluckingModification)

    return OrderedDict([('palm_mute', plucking_mod.palm_mute),
                        ('artificial_harmonic',
                         ArtificialHarmonic_to_dict(
                             plucking_mod.artificial_harmonic))])


def dict_to_PluckingModification(plucking_mod_dict):

    return datatypes.PluckingModification(
        plucking_mod_dict['palm_mute'],
        dict_to_ArtificialHarmonic(plucking_mod_dict['artificial_harmonic']))


def ArtificialHarmonic_to_dict(artificial_harmonic):
    """ convert the artificial harmonic namedtuple to a dict
    """
    octave = None
    pitch = None
    if isinstance(artificial_harmonic, datatypes.ArtificialHarmonic):
        if artificial_harmonic.octave == guitarpro.models.Octave(0):
            octave = 0
        if artificial_harmonic.octave == guitarpro.models.Octave(1):
            octave = 1
        if artificial_harmonic.octave == guitarpro.models.Octave(2):
            octave = 2
        if artificial_harmonic.octave == guitarpro.models.Octave(3):
            octave = 3
        if artificial_harmonic.octave == guitarpro.models.Octave(4):
            octave = 4

        pitch = OrderedDict(
            [('just', artificial_harmonic.pitch.just),
             ('accidental', artificial_harmonic.pitch.accidental),
             ('value', artificial_harmonic.pitch.value),
             ('intonation', artificial_harmonic.pitch.intonation)])

    return OrderedDict([('octave', octave), ('pitch', pitch)])


def dict_to_ArtificialHarmonic(artificial_harmonic_dict):

    #ah_params = list(set(artificial_harmonic_dict.values()))
    #if len(ah_params) == 1:
    #    if ah_params[0] is None:
    if check_none_value(artificial_harmonic_dict):
        return None
    else:
        return datatypes.ArtificialHarmonic(
            guitarpro.models.Octave(artificial_harmonic_dict['octave']),
            guitarpro.models.PitchClass(
                just=artificial_harmonic_dict['pitch']['just'],
                accidental=artificial_harmonic_dict['pitch']['accidental'],
                value=artificial_harmonic_dict['pitch']['value'],
                intonation=artificial_harmonic_dict['pitch']['intonation']))


def FrettingAdornment_to_dict(fretting):
    """ convert FrettingAdornment namedtuple to dict
    """
    assert isinstance(fretting, datatypes.FrettingAdornment)

    return OrderedDict([('technique', fretting.technique),
                        ('modification',
                         FrettingModification_to_dict(fretting.modification)),
                        ('accent',
                         fretting.accent), ('modulation',
                                            Modulation_to_dict(
                                                fretting.modulation))])


def dict_to_FrettingAdornment(fretting_dict):

    fretting_technique = str(fretting_dict['technique'])
    if fretting_technique == 'None':
        fretting_technique = None
    return datatypes.FrettingAdornment(
        fretting_technique,
        dict_to_FrettingModification(
            fretting_dict['modification']), fretting_dict['accent'],
        dict_to_Modulation(fretting_dict['modulation']))



def FrettingModification_to_dict(fretting_modification):
    """ convert FrettingModification namedtuple to dict
    """
    assert isinstance(fretting_modification, datatypes.FrettingModification)
    return OrderedDict([('type', fretting_modification.type),
                        ('let_ring', fretting_modification.let_ring)])


def dict_to_FrettingModification(fretting_modification_dict):

    return datatypes.FrettingModification(
        fretting_modification_dict['type'],
        fretting_modification_dict['let_ring'])


def Modulation_to_dict(modulation):
    """ convert Moduation namedtuple to dict
    """

    return OrderedDict([('bend', Bend_to_dict(
        modulation.bend)), ('vibrato', modulation.vibrato),
                        ('trill', Trill_to_dict(modulation.trill)),
                        ('slide', Slide_to_dict(modulation.slide))])


def dict_to_Modulation(modulation_dict):

    return datatypes.Modulation(
        dict_to_Bend(modulation_dict['bend']), modulation_dict['vibrato'],
        dict_to_Trill(modulation_dict['trill']),
        dict_to_Slide(modulation_dict['slide']))


def Bend_to_dict(bend):
    """ convert Bend namedtuple to dict
    """
    bend_type = None
    bend_value = None
    bend_points = []

    if isinstance(bend, datatypes.Bend):
        bend_type = bend.type
        bend_value = bend.value
        for bend_point in bend.points:
            bend_points.append(BendPoint_to_dict(bend_point))

    return OrderedDict([('type', bend_type), ('value', bend_value),
                        ('points', bend_points)])


def dict_to_Bend(bend_dict):
    if bend_dict['type'] is None:
        return None
    else:
        bend_points = []
        for bend_point_dict in bend_dict['points']:
            bend_points.append(dict_to_BendPoint(bend_point_dict))
        return datatypes.Bend(
            type=bend_dict['type'],
            value=bend_dict['value'],
            points=bend_points)


def BendPoint_to_dict(bend_point):
    """ convert BendPoint namedtuple to dict
    """
    assert isinstance(bend_point, datatypes.BendPoint)

    return OrderedDict([('position', bend_point.position),
                        ('value', bend_point.value), ('vibrato',
                                                      bend_point.vibrato)])


def dict_to_BendPoint(bend_point_dict):
    return datatypes.BendPoint(bend_point_dict['position'],
                               bend_point_dict['value'],
                               bend_point_dict['vibrato'])


def Trill_to_dict(trill):
    """ convert Trill namedtuple to dict
    """
    fret = None
    notated_duration = None
    if isinstance(trill, datatypes.Trill):
        fret = trill.fret
        notated_duration = NotatedDuration_to_dict(trill.notated_duration)

    return OrderedDict([('fret', fret), ('notated_duration',
                                         notated_duration)])


def dict_to_Trill(trill_dict):

    if check_none_value(trill_dict):
        return None
    else:
        return datatypes.Trill(
            trill_dict['fret'],
            dict_to_NotatedDuration(trill_dict['notated_duration']))


def Slide_to_dict(slide):
    """ convert Slide namedtuple to dict
    """
    into = None
    outto = None
    if isinstance(slide, datatypes.Slide):
        into = slide.into
        outto = slide.outto
    return OrderedDict([('into', into), ('outto', outto)])


def dict_to_Slide(slide_dict):
    if check_none_value(slide_dict):
        return None
    else:
        return datatypes.Slide(slide_dict['into'], slide_dict['outto'])


def GraceNote_to_dict(grace_note):
    """ convert GraceNote namedtuple to dict
    """
    fret = None
    duration = None
    dynamic = None
    dead_note = None
    on_beat = None
    transition = None

    if isinstance(grace_note, datatypes.GraceNote):
        fret = grace_note.fret
        duration = fraction_to_dict(grace_note.duration)
        dynamic = Dynamic_to_dict(grace_note.dynamic)
        dead_note = grace_note.dead_note
        on_beat = grace_note.on_beat
        transition = grace_note.transition

    return OrderedDict([('fret', fret), ('duration', duration),
                        ('dynamic', dynamic), ('dead_note', dead_note),
                        ('on_beat', on_beat), ('transition', transition)])


def dict_to_GraceNote(grace_note_dict):

    # test if all the parameters are None
    #grace_note_params = list(set(grace_note_dict.values()))
    #if len(grace_note_params) == 1 or grace_note_dict is None:
    #    if grace_note_params[0] is None:
    #        return None

    if check_none_value(grace_note_dict):
        return None
    else:
        return datatypes.GraceNote(grace_note_dict['fret'],
                                   dict_to_fraction(grace_note_dict['duration']),
                                   dict_to_Dynamic(grace_note_dict['dynamic']),
                                   grace_note_dict['dead_note'],
                                   grace_note_dict['on_beat'],
                                   grace_note_dict['transition'])


def check_none_value(api_dict):

    values = []
    for value in api_dict:
        if api_dict[value] not in values:
            values.append(api_dict[value])

    if len(values) == 1:
        if values[0] is None:
            return True
    else:
        return False


def fraction_to_dict(fraction):

    return OrderedDict([('numerator', fraction.numerator), ('denominator', fraction.denominator)])


def dict_to_fraction(fraction_dict):

    return Fraction(fraction_dict['numerator'], fraction_dict['denominator'])
