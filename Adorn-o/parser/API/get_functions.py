'''
These are the set of functions that retrieves data from guitarpro's
.GP5 files and from JSON files
'''

# Standard library imports
from fractions import Fraction
import json

# Third party imports
import guitarpro

# Local application imports
import parser
from .calculate_functions import calculate_note_pitch, calculate_duration_for_notes_in_song, calculate_triplet_feel_note_durations, calculate_polyphony_for_measures_in_a_song
from . import datatypes
from .update_functions import update_note
from . import dict_conversion as dict2api


def get_from_JSON(json_dict):
    """ get the API data from an JSON dict

    """
    if 'tracks' in list(json_dict.keys()):
        return dict2api.dict_to_tracks(json_dict)
    elif 'song' in list(json_dict.keys()):
        return dict2api.dict_to_Song(json_dict)
    elif 'notes' in list(json_dict.keys()) and 'start_time' in list(json_dict.keys(
    )) and 'meta_data' in list(json_dict.keys()):
        return dict2api.dict_to_Measure(json_dict)
    elif 'adorned_note' in list(json_dict.keys()):
        return dict2api.dict_to_AdornedNote(json_dict)
    elif 'rest' in list(json_dict.keys()):
        return dict2api.dict_to_Rest(json_dict)


def get_rest_data(note_number, beat):
    '''
    Get the rest data from GP5 beat data structure
    '''

    return datatypes.Rest(note_number, get_start_time(beat), None,
                          get_beat_duration(beat))


# TODO: This needs to be updated to reflect it is getting pitch
# information about the note.
def get_note_data(note_number, beat, note, track, midinote=None):
    '''
    Gets the data for the note, on a specific beat, this includes:
     - fret_number
     - string_number
     - string tuning
     - start_time
     - duration
     - dynamic
    '''

    fret_number = get_note_fret_number(note)
    string_number = get_string_number(note)
    string_tuning = get_string_tunings(track)
    start_time = get_start_time(beat)
    duration = None
    notated_duration = get_notated_duration(beat.duration)
    dynamic = get_note_dynamic(note, beat)

    if not midinote:
        return datatypes.Note(note_number, None, fret_number, string_number,
                              string_tuning, start_time, duration,
                              notated_duration, dynamic)
    else:
        return datatypes.Note(note_number, midinote, fret_number,
                              string_number, string_tuning, start_time,
                              duration, notated_duration, dynamic)


# Gets the fret number of a note
def get_note_fret_number(note):
    ''' Gets the fret number of a note '''

    return note.value


# Gets the string number for a note
def get_string_number(note):
    ''' Gets the string number for a note '''

    return note.string


# Gets the note dynamic
def get_note_dynamic(note, beat):
    '''Gets the note dynamic'''
    cres_dim = None
    if beat.text:
        if beat.text.value.find("cres") != -1 or beat.text.value.find(
                "cres.") != -1 or beat.text.value.find(
                    "cresc") != -1 or beat.text.value.find("cresc.") != -1:
            cres_dim = 'cresc'
        elif beat.text.value.find("dim") != -1 or beat.text.value.find(
                "dim.") != -1:
            cres_dim = 'dim'

    return datatypes.Dynamic(
        parser.utilities.dynamic.get(note.velocity), cres_dim)


# Gets the start time relative to the very start of the piece
# Always starts at 960 (midi ticks? ms?) - or is the end of each note
# 960 = quater note
# so to get the start time in beats its beat.start / 960
# Notes:
# - This doesn't take into concideration swing.
# - So any offests will need to be calculated and this value adjusted.
#
# This function will check if a beat or measure is passed into it
# and read the relevent information from each and convert it accordingly.
def get_start_time(beat_or_measure):
    '''
    Check is a beat or measure is passed into this function.
    Read the start time, and convert from midi ticks to metric beats.
    '''
    if type(beat_or_measure) == guitarpro.models.Beat:
        return (Fraction(beat_or_measure.start, 960) / 4 - Fraction(1, 4))
    if type(beat_or_measure) == guitarpro.models.Measure:
        return (
            Fraction(beat_or_measure.header.start, 960) / 4 - Fraction(1, 4))


# Gets the duration of a beat.
def get_beat_duration(beat):

    return get_notated_duration(beat.duration)


def get_notated_duration(duration):
    '''
    Get the duration data from GP5 duration datatype
    '''
    if duration.value is not None:
        return datatypes.NotatedDuration(
            Fraction(1, duration.value), duration.isDotted,
            False, #duration.isDoubleDotted,
            datatypes.Tuplet(duration.tuplet.enters, duration.tuplet.times))
    else:
        return datatypes.NotatedDuration(
            Fraction(1, 64), duration.isDotted, duration.isDoubleDotted,
            datatypes.Tuplet(duration.tuplet.enters, duration.tuplet.times))


def get_string_tunings(track):
    string_tuning = {}
    for string in track.strings:

        # fills the dictionary with string number
        # and its tuning in midi
        string_tuning[string.number] = string.value

    return string_tuning


# def get_beat_number(flag):
#    return flag


# Get adornment function
# Basic implementation that just gets the adornments for a note,
# at a given beat, with specific hammer-on, pull-off information
# Returns:
# <adornment> ::=
#               <plucking_adornments>,
#               < fretting_adornments>,
#               <grace_note>,
#               <ghost_note>
def get_adornments(beat, note, hammerpullinfo):
    adornments = datatypes.Adornment(
        get_plucking_adornment(beat, note),
        get_fretting_adornment(beat, note, hammerpullinfo),
        get_grace_note(note, beat), get_ghost_note(note))
    return adornments


def get_grace_note(note, beat):
    if note.effect.grace is None:
        grace_note = None
    else:
        transition = None
        if guitarpro.models.GraceEffectTransition.none == note.effect.grace.transition:
            transition = None
        if guitarpro.models.GraceEffectTransition.slide == note.effect.grace.transition:
            transition = "slide"
        if guitarpro.models.GraceEffectTransition.bend == note.effect.grace.transition:
            transition = "bend"
        if guitarpro.models.GraceEffectTransition.hammer == note.effect.grace.transition:
            transition = "hammer"

        grace_duration = Fraction(1, note.effect.grace.duration)
        #if note.effect.grace.duration > 64:
        #    grace_duration = Fraction(1, 64)

        grace_note = datatypes.GraceNote(
            note.effect.grace.fret, grace_duration,
            get_note_dynamic(note.effect.grace, beat),
            note.effect.grace.isDead, note.effect.grace.isOnBeat, transition)

    return grace_note


def get_ghost_note(note):

    return note.effect.ghostNote


# Gets the plucking adornments for a note
# <plucking_adornment> :=
#               <plucking_technique>,
#               <plucking_modification>,
#               <plucking_accent>
def get_plucking_adornment(beat, note):

    accent = get_plucking_accent(note, beat)
    assert isinstance(accent, bool)
    return datatypes.PluckingAdornment(
        get_plucking_technique(beat, note), get_plucking_modification(note),
        accent)


# Gets the Plucking technique
# <plucking_technique> := 'finger' | 'tied' | 'pick' | 'pick_up' | 'pick_down'
#                           | 'slap' | 'pop' | 'tap'
#                           | 'double_thumb' | 'double_thumb_upstroke'
#                           | 'double_thumb_downstroke' | "double_stop"
#                           | "3_note_chord" | "4_note_chord"
#                           : default = 'finger'
def get_plucking_technique(beat, note):

    if (beat.effect.slapEffect == guitarpro.SlapEffect.none
            and beat.status == guitarpro.BeatStatus.normal
            and note.type != guitarpro.NoteType.rest
            and note.type != guitarpro.NoteType.tie
            and beat.effect.pickStroke == guitarpro.BeatStrokeDirection.none
            and len(beat.notes) < 2):
        return 'finger'
    elif note.type == guitarpro.NoteType.tie:
        return 'tied'
    elif len(beat.notes) == 2:
        return "double_stop"
    elif len(beat.notes) == 3:
        return "3_note_chord"
    elif len(beat.notes) == 4:
        return "4_note_chord"
    elif (beat.effect.pickStroke != guitarpro.BeatStrokeDirection.none
          and beat.effect.slapEffect == guitarpro.SlapEffect.none):
        if beat.effect.pickStroke == guitarpro.BeatStrokeDirection.down:
            return 'pick_down'
        elif beat.effect.pickStroke == guitarpro.BeatStrokeDirection.up:
            return 'pick_up'
        else:
            return 'pick'
    elif (beat.effect.slapEffect != guitarpro.SlapEffect.none):
        # print 'Some Slapping....'
        if (beat.effect.slapEffect == guitarpro.SlapEffect.slapping and
                beat.effect.pickStroke == guitarpro.BeatStrokeDirection.none):
            # print 'Slap Thumb'
            return 'slap'
        elif (beat.effect.slapEffect == guitarpro.SlapEffect.slapping and
              beat.effect.pickStroke != guitarpro.BeatStrokeDirection.none):
            if beat.effect.pickStroke == guitarpro.BeatStrokeDirection.down:
                return 'double_thumb_downstroke'
            elif beat.effect.pickStroke == guitarpro.BeatStrokeDirection.up:
                return 'double_thumb_upstroke'
            return 'double_thumb'

        elif (beat.effect.slapEffect == guitarpro.SlapEffect.popping):
            # print 'Pop'
            return 'pop'

        elif (beat.effect.slapEffect == guitarpro.SlapEffect.tapping):
            # print 'Tap'
            return 'tap'


# Checks the plucking modifications in the note
# and returns the corresponding flag
# <plucking_modification> ::= None | <artificial_harmonic> | "palm_mute"
def get_plucking_modification(note):

    ah = None
    pm = False
    if type(note.effect.harmonic) == guitarpro.models.ArtificialHarmonic:
        # Needs to get the artificial harmonic data:
        # which is <octave offset>, <artificial_harmonic_interval>
        ah = get_artificial_harmonic_data(note)
    if note.effect.palmMute:
        pm = True

    return datatypes.PluckingModification(pm, ah)


# Gets the plucking accent information from the note
# Returns true if the note is accented, false if it is not
# <plucking_accent> ::= <boolean>
def get_plucking_accent(note, beat):

    if note.effect.accentuatedNote:
        # check to see if there is text indicating the
        # accent is only meant to be stacatto
        # to correct gp5 exporting issues

        if beat.text:
            if beat.text.value.find('St') >= 0:
                return False
        else:
            return True
    else:
        return False


# Gets the interval increase for the artificial harmonic
# Todo: possibly work out the interval increase to the fretted
# note are return that.
#
# Returns [harmonic octave, pitch interval]
def get_artificial_harmonic_data(note):
    if type(note.effect.harmonic) == guitarpro.models.ArtificialHarmonic:
        return datatypes.ArtificialHarmonic(note.effect.harmonic.octave,
                                            note.effect.harmonic.pitch)
    else:
        return 0


# Get fretting Adornment Function
# returns the fretting adornment data structure
# <fretting_adornment> ::= <fretting_technique> , <fretting_modification>,
#                           <frettnig_accent>, <modulation>
def get_fretting_adornment(beat, note, hammerpullinfo):

    return datatypes.FrettingAdornment(
        get_fretting_technique(beat, note, hammerpullinfo),
        get_fretting_modification(note), get_fretting_accent(note.effect),
        get_modulation(note))


# Get fretting technique:
# <fretting_technique> ::= None | 'fretting' | 'hammer-on'
#                           | 'pull-off' | 'left-handed-slap'
#                           ; default = None
def get_fretting_technique(beat, note, hammerpullinfo):

    # Sets hp_vals to be the default of 'none'
    # if there is a hp (hammer-on/pull-off) value
    # this will be updated with the string/ fret pairing infomation.
    hp_vals = 'none'

    # For each string/note value in the hammer-on pull off information:
    # check that it matched the current string:
    #   - If it does store the values
    #   - Then check if the current note.value is higher
    #   or lower than the hp_val
    #    - if the note.value is:
    #       - Lower = Pull-off
    #       - Higher = Hammer-on
    for x in hammerpullinfo:
        if x[0] == note.string:
            hp_vals = x
        if hp_vals != 'none':
            if hp_vals[0] == note.string and hp_vals[1] < note.value:
                return 'hammer-on'
            if hp_vals[0] == note.string and hp_vals[1] > note.value:
                return 'pull-off'

    # Basic checks on the note.value (aka fret)
    # If its 0 the open string is played
    # if its not, the note is fretted, if there is some additional
    # text this will indicate a left hand slap, with an additional check
    # to ensure the right text tag was used to indicate this technique.
    if note.value == 0:
        return None
    elif note.value > 0:
        if beat.text:
            if beat.text.value.find("lh") != -1 or beat.text.value.find(
                    "LH") != -1:
                return "left-hand-slap"
        return 'fretting'


# Gets the fretting modification
# <fretting_modification> ::=  'none' | 'natural-harmonic' | ' dead-note' |
#                               'let-ring' ; default = 'none'
def get_fretting_modification(note):
    mod = None
    let_ring = False

    if note.effect.harmonic:
        if type(note.effect.harmonic) == guitarpro.models.NaturalHarmonic:
            mod = "natural-harmonic"
    elif note.type == guitarpro.NoteType.dead:
        mod = 'dead-note'
    if note.effect.letRing:
        let_ring = True

    return datatypes.FrettingModification(mod, let_ring)


# Get fretting accent
# Checks the note_effect.staccato which is a true/false
# flag in Guitar pro and returns its value.
# <fretting_accent> ::= <boolean> ; default = False
def get_fretting_accent(note_effect):

    if note_effect.staccato:
        return True
    else:
        return False


# Get modulation adornment:
# This includes:
#       - Bend
#       - Vibrato
#       - Trill
#       - Slide
# And calls the relative functions
# There can only be one type of modulation applied to a note at
# a given time
# <modulation> ::= none | <vibrato> | <bend> | <trill> | <slide>
#                   ; default = none
def get_modulation(note):

    return datatypes.Modulation(
        get_bend(note), get_vibrato(note), get_trill(note), get_slide(note))


# Gets the bend data for the note:
# <bend> ::=
#           <bend_type> , <bend_value>, <bend_points>
# <bend_type> ::=
#           'bend' | 'bend_release' | 'pre_bend' | 'pre_bend_bend' |
#           'pre_bend_release' ; default = 'bend'
# <bend_value> ::= <float> ; default = 0.0
# <bend_points> ::= 1*<bend_point>
# <bend_point> ::=
#     <bend_point_position>, <bend_point_value>, <bend_point_vibrato>
# <bend_point_position> ::=
# <bend_point_value> ::= <float> ; default = 0.0
# <bend_point_vibrato> ::= <boolean> ; default = False
def get_bend(note):
    # if there is no bend data return
    if not note.effect.bend:
        return
    # bend type =
    if note.effect.bend.type is guitarpro.models.BendType.bend:
        bend_type = 'bend'
    elif note.effect.bend.type is guitarpro.models.BendType.bendRelease:
        bend_type = 'bend_release'
    elif note.effect.bend.type is guitarpro.models.BendType.prebend:
        # Need to check the bend points to determine if this
        # is a prebend or prebendbend
        bend_type = 'pre_bend'
    elif note.effect.bend.type is guitarpro.models.BendType.prebendRelease:
        bend_type = 'pre_bend_release'
    elif note.effect.bend.type is guitarpro.models.BendType.bendReleaseBend:
        bend_type = 'bend_release_bend'
    else:
        bend_type = 'bend'

    # bend value =
    bend_value = note.effect.bend.value

    # bend points =
    # Need to loop through the bend points to get each point
    # then append them to the bend point list
    bend_points = []
    for point in note.effect.bend.points:
        bend_points.append(
            datatypes.BendPoint(point.position, point.value, point.vibrato))

    # Returns the bend data
    return datatypes.Bend(bend_type, bend_value, bend_points)


# Gets vibrato data:
# <vibrato> ::= <boolean> ; default = False
def get_vibrato(note):
    return note.effect.vibrato


# Gets Trill data:
# <tril> ::= <trill_fret>, <trill_duration>
# <trill-fret> ::= <fret_number>
# <trill_duration> ::=
#       <trill_note_value>, <isDotted> <isDoubleDotted>, <tuplet>
# <trill_note_value> ::=
# <tuplet> ::=
# note: Need to convert tuplet into a fraction/adjust as
# needed. Notable when calculating the trill notes.
def get_trill(note):
    # if trill is empty return
    if not note.effect.trill:
        return
    return datatypes.Trill(note.effect.trill.fret,
                           get_notated_duration(note.effect.trill.duration))
    #                       datatypes.Duration(
    #                        note.effect.trill.duration.value,
    #                        note.effect.trill.duration.isDotted,
    #                        note.effect.trill.duration.isDoubleDotted,
    #                        note.effect.trill.duration.tuplet))


# <slide> ::= 'slide_shift_to' | 'slide_from_above' | 'slide_from_below'
#            'slide_out_below' | 'slide_out_above' | 'slide_legato'
def get_slide(note):

    # get the slides for the note.
    slides = note.effect.slides

    # Some reason this is a list of slides.
    # not sure why. Not sure you can have multiple slides for a note
    # So added a check just incase

    slide_data = datatypes.Slide(None, None)
    if len(slides) is not 0:
        for slide in slides:
            if slide == guitarpro.models.SlideType.shiftSlideTo:
                slide_data = slide_data._replace(outto='slide_shift_to')
            if slide == guitarpro.models.SlideType.intoFromAbove:
                slide_data = slide_data._replace(into='slide_from_above')
            if slide == guitarpro.models.SlideType.intoFromBelow:
                slide_data = slide_data._replace(into='slide_from_below')
            if slide == guitarpro.models.SlideType.outDownwards:
                slide_data = slide_data._replace(outto='slide_out_below')
            if slide == guitarpro.models.SlideType.outUpwards:
                slide_data = slide_data._replace(outto='slide_out_above')
            if slide == guitarpro.models.SlideType.legatoSlideTo:
                slide_data = slide_data._replace(outto='slide_legato')
            # if slides[0] == guitarpro.models.SlideType.none:
            # return
        return slide_data
    else:
        return


# Get measure
# <measure> ::= <measure_meta_data>, <start_time>, [<adorned_note>]
#              | <measure_meta_data>, <start_time>, [<note>]
#              | <measure_meta_data>, <start_time>, [<adornments>]
def get_measure_data(song,
                     measure_to_get_data_for,
                     hampullfrom=[],
                     slide_from=[],
                     previous_beat_notes=[]):

    measure_meta_data = []
    measure_start_time = 0
    measure_notes = []

    beat_number = 0
    note_number = 0

    # Stores the hammer-on-pull-off and slide data from previous notes
    hampullfrom = hampullfrom
    # Note: slide from information is likely not being used.
    slide_from = slide_from

    # This stores the prevous notes
    previous_beat_notes = previous_beat_notes

    for track in song.tracks:
        if parser.utilities.midi2BassType.get(track.channel.instrument):
            for measure in track.measures:
                if measure.header.start == measure_to_get_data_for.header.start:
                    measure_start_time = get_start_time(measure)
                    measure_meta_data = get_measure_meta_data(song, measure)
                    for voice in measure.voices:
                        for beat in voice.beats:
                            # Check that the beat isn't empty
                            # if beat.status is guitarpro.BeatStatus.empty:
                            #    print "EMPTY NOTE!!!"
                            #    print beat
                            #    print get_start_time(beat)
                            #    print measure_start_time
                            if beat.status != guitarpro.BeatStatus.empty:
                                # Counts the beats
                                beat_number += 1

                                # Store Hammer-on/Pull off information and reset it:
                                hp_info = hampullfrom
                                hampullfrom = []

                                # Store slide info and reset it
                                slide_info = slide_from
                                slide_from = []

                                # store previous beat notes
                                tied_to = previous_beat_notes
                                previous_beat_notes = []

                                # Get all the information for each note
                                # in sequential order.
                                for note in beat.notes:

                                    # increment the note_number
                                    note_number = note_number + 1

                                    # Get next note Hammer-on / pull off information
                                    # True indicates that the next note is a hammer-on or pull off
                                    if (note.effect.hammer == True):
                                        # print 'Next Note is a hammer-on or a Pull-off'
                                        hampullfrom.append(
                                            [note.string, note.value])
                                    if note.effect.slides:
                                        slide_from.append([
                                            note.string, note.value,
                                            note.effect.slides
                                        ])

                                    note_adornments = get_adornments(
                                        beat, note, hp_info)
                                    #print note
                                    #print note_adornments

                                    fret = get_note_fret_number(note)
                                    # check if the note is tied:
                                    if note_adornments.plucking.technique is "tied":
                                        # a tied note has no fret value,
                                        # only the string
                                        # check the previous notes and find
                                        # what note it is tied to.
                                        for prev_note in tied_to:
                                            if (prev_note.string_number ==
                                                    get_string_number(note)):
                                                fret = prev_note.fret_number
                                    #else:
                                    #    fret = get_note_fret_number(note)

                                    # Calculate Midi Note
                                    midinote = calculate_note_pitch(
                                        fret, get_string_number(note),
                                        get_string_tunings(track),
                                        get_fretting_modification(note),
                                        get_plucking_adornment(beat, note)[1])
                                    # midinote = calculate_note_pitch(
                                    #                           note.value,
                                    #                           note.string,
                                    #                           string_tuning,
                                    #                           harmonic_data)
                                    note_data = get_note_data(
                                        note_number, beat, note, track,
                                        midinote)
                                    # update the fret to be correct
                                    note_data = update_note(
                                        note_data, fret_number=fret)

                                    # see if dynamics need to be corrected

                                    if song.instructions == "correct_dynamics":
                                        if note_adornments.plucking.accent or note_adornments.fretting.accent:
                                            # increment the dynamic by one volume level
                                            if note_data.dynamic.value == 'ppp':
                                                new_dynamic = datatypes.Dynamic(
                                                    'pp',
                                                    note_data.dynamic.cres_dim)
                                            elif note_data.dynamic.value == 'pp':
                                                new_dynamic = datatypes.Dynamic(
                                                    'p',
                                                    note_data.dynamic.cres_dim)
                                            elif note_data.dynamic.value == 'p':
                                                new_dynamic = datatypes.Dynamic(
                                                    'mp',
                                                    note_data.dynamic.cres_dim)
                                            elif note_data.dynamic.value == 'mp':
                                                new_dynamic = datatypes.Dynamic(
                                                    'mf',
                                                    note_data.dynamic.cres_dim)
                                            elif note_data.dynamic.value == 'mf':
                                                new_dynamic = datatypes.Dynamic(
                                                    'f',
                                                    note_data.dynamic.cres_dim)
                                            elif note_data.dynamic.value == 'f':
                                                new_dynamic = datatypes.Dynamic(
                                                    'ff',
                                                    note_data.dynamic.cres_dim)
                                            elif note_data.dynamic.value == 'ff':
                                                new_dynamic = datatypes.Dynamic(
                                                    'fff',
                                                    note_data.dynamic.cres_dim)
                                            elif note_data.dynamic.value == 'fff':
                                                new_dynamic = datatypes.Dynamic(
                                                    'fff',
                                                    note_data.dynamic.cres_dim)

                                            note_data = update_note(
                                                note_data, dynamic=new_dynamic)

                                    # append the note to previous_beat_notes
                                    previous_beat_notes.append(note_data)

                                    # combine the adornments and note into
                                    # an adorned note, then append to the
                                    # measure_notes.
                                    measure_notes.append(
                                        datatypes.AdornedNote(
                                            note_data, note_adornments))

                                if beat.status == guitarpro.BeatStatus.rest:
                                    # increment the note_number
                                    note_number = note_number + 1
                                    measure_notes.append(
                                        get_rest_data(note_number, beat))

    return datatypes.Measure(
        measure_meta_data, measure_start_time,
        measure_notes), hampullfrom, slide_from, previous_beat_notes


# Get measure meta data
# <measure_meta_data> ::= <song_title>, <measures_number>,
#                              <key_signature>, <time_signature>, <tempo>,
#                              <triplet_feel>
def get_measure_meta_data(song, measure):
    return datatypes.MeasureMetaData(
        get_song_title(song), get_measure_number(measure),
        get_key_signature(measure), get_timesignature(measure),
        #get_tempo(measure), get_triplet_feel(measure), None, None, None)
        song.tempo, get_triplet_feel(measure), None, None, None)


# Get song title
def get_song_title(song):
    return song.title.replace(' ', '-')


def get_song_artist(song):
    return song.artist.replace(' ', '-')


# get measure_number
def get_measure_number(measure):
    return measure.header.number


# Get key signature
# GP5 form = KeySignature.<key_sig_name>
# This is converted to a str, split at the "."
# and then key signature name is then returned.
def get_key_signature(measure):
    return str(measure.header.keySignature).split('.')[1]


# Get time signature
def get_timesignature(measure):
    return (str(measure.header.timeSignature.numerator) + '/' + str(
        measure.header.timeSignature.denominator.value))


# Get triplet feel
def get_triplet_feel(measure):

    if measure.header.tripletFeel == guitarpro.TripletFeel.sixteenth:
        return "16th"
    elif measure.header.tripletFeel == guitarpro.TripletFeel.eighth:
        return "8th"
    else:
        return None


# Get Tempo
# this is slightly more complex as there is a variable tempo
# that is changeable in the beat.effect.MixTableChange.tempo.value
# also need to convert guitarpro.Tempo to int
def get_tempo(song):
    #return measure.header.tempo.value
    return song.tempo


# Get's the song data from guitar pro data structure
# <song> ::= <song_meta_data>, [<measure>]
def get_song_data(song):
    songs = []
    # check the number of bass tracks
    if len(get_bass_track_numbers(song)) == 1:
        song_data = datatypes.Song(
            get_song_meta_data(song), get_song_measures(song))
        # calculate the durations, tripletfeel and polyphony for the song
        calculate_duration_for_notes_in_song(song_data)
        # calculate_triplet_feel_note_durations(song_data)
        calculate_polyphony_for_measures_in_a_song(song_data)
        songs.append(song_data)
    else:
        # get the bass tracks:
        bass_tracks = get_bass_track_numbers(song)
        for bass_track in bass_tracks:
            song_data = datatypes.Song(
                get_song_meta_data(song, bass_track),
                get_song_measures(song, bass_track))
            # calculate the durations, tripletfeel and polyphony for the song
            calculate_duration_for_notes_in_song(song_data)
            # calculate_triplet_feel_note_durations(song_data)
            calculate_polyphony_for_measures_in_a_song(song_data)
            songs.append(song_data)

    return songs


# Get song meta data
# <song_meta_data> ::= <song_title>, <number_of_measures>
def get_song_meta_data(song, multi_track=False):
    # returns the song title and then the number
    # of measures in the first track.
    if multi_track is False:
        return datatypes.SongMetaData(
            get_song_artist(song), get_song_title(song), song.tempo,
            str(song.key).split('.')[1], len(song.tracks[0].measures))
    else:
        return datatypes.SongMetaData(
            get_song_artist(song),
            get_song_title(song) + '_track_' + str(multi_track), song.tempo,
            str(song.key).split('.')[1], len(song.tracks[0].measures))


# Get song measures
def get_song_measures(song, track_number=False):
    '''
    gets the measure data from a gp5 song data structure

    if track_number is set to false, then the information from
    the bass track within the song is returned

    if track_number is set to a number, the information from the
    specified track is returned if it is also a bass track.
    '''
    song_measures = []
    if track_number is False:
        for track in song.tracks:
            if parser.utilities.midi2BassType.get(track.channel.instrument):
                # setup parameters to keep track of previous notes:
                # that could indicate an adorment for the next note
                # that happens to be in the next bar:
                hampullfrom = []
                slide_from = []
                previous_beat_notes = []
                measure_number = 1
                for measure in track.measures:
                    # get the measure data:
                    measure_data = get_measure_data(song, measure, hampullfrom,
                                                    slide_from,
                                                    previous_beat_notes)
                    # Append the measure to the song_measures
                    song_measures.append(measure_data[0])
                    # update previous note parameters:
                    hampullfrom = measure_data[1]
                    slide_from = measure_data[2]
                    previous_beat_notes = measure_data[3]
                    measure_number += 1
    else:
        track_count = 0
        for track in song.tracks:
            track_count += 1
            if track_count == track_number:
                if parser.utilities.midi2BassType.get(
                        track.channel.instrument):
                    # setup parameters to keep track of previous notes:
                    # that could indicate an adorment for the next note
                    # that happens to be in the next bar:
                    hampullfrom = []
                    slide_from = []
                    previous_beat_notes = []
                    measure_number = 1
                    for measure in track.measures:
                        # get the measure data:
                        measure_data = get_measure_data(
                            song, measure, hampullfrom, slide_from,
                            previous_beat_notes)
                        # Append the measure to the song_measures
                        song_measures.append(measure_data[0])
                        # update previous note parameters:
                        hampullfrom = measure_data[1]
                        slide_from = measure_data[2]
                        previous_beat_notes = measure_data[3]
                        measure_number += 1

    return song_measures


def get_bass_track_numbers(song):
    bass_tracks = []
    track_number = 0
    for track in song.tracks:
        if parser.utilities.midi2BassType.get(track.channel.instrument):
            track_number += 1
            bass_tracks.append(track_number)
    return bass_tracks
