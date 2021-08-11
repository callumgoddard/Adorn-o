'''
Functions to write the API data into guitarpro data structures
'''

# Standard library imports
from fractions import Fraction
import json

# Third party imports
import guitarpro

# Local application imports
import datatypes
import parser.utilities as utilities
import dict_conversion as api2dict


def api_to_json(api_song):
    """ convert the output from the get_song_data function
    directly into json, not needing to account for tracks.
    """
    dict_song = api2dict.tracks_to_dict(api_song)
    return json.dumps(dict_song, indent=4), dict_song


def Song_to_json(api_song):
    """ convert the Song namedtuple into json, this is if the
    output from the get_song_data function has been broken down
    into its individual Song tracks.
    """

    dict_song = api2dict.Song_to_dict(api_song)
    return json.dumps(dict_song, indent=4), dict_song


def Measure_to_json(api_measure_input):
    """ convert the Measure namedtuple into json, Song namedtuple
    has been broken down into its individual measures.
    """

    dict_song = api2dict.Measure_to_dict(api_measure_input)
    return json.dumps(dict_song, indent=4)


def api_to_gp5(apisong_input, gp5song):
    '''
    Update the gp5 song data with the API song information

    Note:
    only run this on the gp5song input ONCE!
    if ran multiple times without reloading the gp5 data from
    a gp5 file there seems to be weird fret changes and things
    with tied notes happening.
    '''

    if not isinstance(apisong_input, list):
        if isinstance(apisong_input, datatypes.Song):
            apisong_input = [apisong_input]

    for apisong in apisong_input:
        assert isinstance(apisong, datatypes.Song)
        # see if the apisong is a specific track in the gp5song:
        if "_track_" in apisong.meta_data.title:
            track_num = apisong.meta_data.title.split("_track_")[-1]
        else:
            track_num = False

        previous_beat = None

        track_count = 0
        for track in gp5song.tracks:
            track_count += 1
            if utilities.midi2BassType.get(track.channel.instrument):

                # if there is a specific track number:
                # skip the tracks until the right one is found
                if track_num:
                    if track_count != track_num:
                        continue

                # reset the measure and note_counts
                measure_count = 0
                note_count = 0
                for measure in track.measures:
                    for voice in measure.voices:
                        for beat in voice.beats:
                            for note in beat.notes:
                                # increment the note count:
                                note_count += 1
                                if (note.type == guitarpro.NoteType.normal or
                                        note.type == guitarpro.NoteType.dead):
                                    # update the note information:
                                    for api_note in apisong.measures[
                                            measure_count].notes:
                                        if isinstance(api_note,
                                                      datatypes.AdornedNote):
                                            if api_note.note.note_number == note_count:

                                                # note there seemd to be an issue
                                                # with some gp5 files fret going wrong...
                                                #print('note.value into converter:', note.value)

                                                beat, note = adornment_to_gp5_note(
                                                    api_note, beat, note)

                                                if previous_beat is not None:
                                                    if (api_note.adornment.
                                                            fretting.technique
                                                            == 'hammer-on' or
                                                            api_note.adornment.
                                                            fretting.technique
                                                            == 'pull-off'):

                                                        for prev_note in previous_beat.notes:
                                                            if prev_note.string == note.string:
                                                                prev_note.effect.hammer = True
                                                                break
                                                    elif (api_note.adornment.
                                                          fretting.technique ==
                                                          'left-handed-slap'):
                                                        beat.text = 'Lh'

                                                break

                            #previous_beat = beat
                    # Update the measure count
                    # Rest the note counter
                    measure_count += 1
                    note_count = 0


def api_start_time_to_gp5(start_time):
    #Fraction(beat_or_measure.start, 960) / 4 - Fraction(1, 4)
    return int(start_time * 960) * 4 + 960


def adornment_to_gp5_note(adorned_note, beat, note):
    assert isinstance(adorned_note,
                      datatypes.AdornedNote), "Must have adorned note as input"
    adornment = adorned_note.adornment

    assert isinstance(
        adornment,
        datatypes.Adornment), "adorned_note adornment is not an Adornment"

    #print('note.value:',note.value)

    beat, note = plucking_technique_to_gp5(adornment, beat, note)
    beat, note = plucking_modification_to_gp5_note(adorned_note, beat, note)
    #print('note.value_after plucking_ mod:',note.value)
    beat, note = plucking_accent_to_gp5_note(adornment, beat, note)
    #beat, note = fretting_technique_to_gp5_note(adornment, beat, note)
    beat, note = fretting_modification_to_gp5_note(adorned_note, beat, note)
    #print('note.value_after fretting_ mod:',note.value)
    beat, note = fretting_accent_to_gp5_note(adornment, beat, note)
    beat, note = modulation_to_gp5_note(adornment, beat, note)
    beat, note = dynamic_to_gp5_note(adorned_note.note, beat, note)

    return beat, note


def plucking_technique_to_gp5(adornment, beat, note):

    # Set up some default values that will change depending on
    # the other technique:
    beat.effect.pickStroke = guitarpro.BeatStrokeDirection.none
    beat.status = guitarpro.BeatStatus.normal
    note.effect.palmMute = False
    note.type = guitarpro.NoteType.normal

    # Convert the plucking adorment
    if adornment.plucking.technique == 'finger':
        beat.effect.slapEffect = guitarpro.SlapEffect.none

    if adornment.plucking.technique == 'pick_down':
        beat.effect.slapEffect = guitarpro.SlapEffect.none
        beat.effect.pickStroke = guitarpro.BeatStrokeDirection.down

    if adornment.plucking.technique == 'pick_up':
        beat.effect.slapEffect = guitarpro.SlapEffect.none
        beat.effect.pickStroke = guitarpro.BeatStrokeDirection.up

    if adornment.plucking.technique == 'slap':
        beat.effect.slapEffect = guitarpro.SlapEffect.slapping

    if adornment.plucking.technique == 'double_thumb_downstroke':
        beat.effect.slapEffect = guitarpro.SlapEffect.slapping
        beat.effect.pickStroke = guitarpro.BeatStrokeDirection.down

    if adornment.plucking.technique == 'double_thumb_upstroke':
        beat.effect.slapEffect = guitarpro.SlapEffect.slapping
        beat.effect.pickStroke = guitarpro.BeatStrokeDirection.up

    if adornment.plucking.technique == 'double_thumb':
        beat.effect.slapEffect = guitarpro.SlapEffect.slapping
        beat.effect.pickStroke = guitarpro.BeatStrokeDirection.up

    if adornment.plucking.technique == 'pop':
        beat.effect.slapEffect = guitarpro.SlapEffect.popping

    if adornment.plucking.technique == 'tap':
        beat.effect.slapEffect = guitarpro.SlapEffect.tapping

    return beat, note


def plucking_modification_to_gp5_note(adorned_note, beat, note):

    adornment = adorned_note.adornment

    note.effect.palmMute = False
    note.effect.harmonic = None

    if adornment.plucking.modification.palm_mute:
        note.effect.palmMute = True

    if isinstance(adornment.plucking.modification.artificial_harmonic,
                  datatypes.ArtificialHarmonic):
        note.effect.harmonic = guitarpro.models.ArtificialHarmonic(
            octave=adornment.plucking.modification.octave,
            pitch=adornment.plucking.modification.pitch)
        # need to update the fret/string too:
        note.value = adorned_note.note.fret_number
        note.string = adorned_note.note.string_number

    return beat, note


def plucking_accent_to_gp5_note(adornment, beat, note):

    note.effect.accentuatedNote = adornment.plucking.accent

    return beat, note


def fretting_technique_to_gp5_note(adornment, beat, note):

    if adornment.fretting.technique == "left-hand-slap":
        beat.text = 'LH'

    return beat, note


def fretting_modification_to_gp5_note(adorned_note, beat, note):

    adornment = adorned_note.adornment
    # set things to defaults:
    note.effect.letRing = False
    note.effect.harmonic = None
    if note.type == guitarpro.NoteType.dead:
        note.type = guitarpro.NoteType.normal

    if adornment.fretting.modification.type == "natural-harmonic":
        note.effect.harmonic = guitarpro.models.NaturalHarmonic()
        # need to update the fret/string too:
        note.value = adorned_note.note.fret_number
        note.string = adorned_note.note.string_number

    if adornment.fretting.modification.type == 'dead-note':
        note.type = guitarpro.NoteType.dead

    if adornment.fretting.modification.let_ring:
        note.effect.letRing = True

    return beat, note


def fretting_accent_to_gp5_note(adornment, beat, note):

    note.effect.staccato = adornment.fretting.accent
    return beat, note


def modulation_to_gp5_note(adornment, beat, note):

    if adornment.fretting.modulation.bend is not None:

        # work out the bend points:
        bend_points = []
        for point in adornment.fretting.modulation.bend.points:
            bend_points.append(
                guitarpro.models.BendPoint(point.position, point.value,
                                           point.vibrato))

        if adornment.fretting.modulation.bend.type == 'bend':
            bend_type = guitarpro.models.BendType.bend
        if adornment.fretting.modulation.bend.type == 'bend_release':
            bend_type = guitarpro.models.BendType.bendRelease
        if adornment.fretting.modulation.bend.type == 'bend_release':
            bend_type = guitarpro.models.BendType.bendRelease
        if adornment.fretting.modulation.bend.type == 'pre_bend':
            bend_type = guitarpro.models.BendType.prebend
        if adornment.fretting.modulation.bend.type == 'pre_bend_release':
            bend_type = guitarpro.models.BendType.prebendRelease
        if adornment.fretting.modulation.bend.type == 'bend_release_bend':
            bend_type = guitarpro.models.BendType.bendReleaseBend

        note.effect.bend = guitarpro.models.BendEffect(
            bend_type, adornment.fretting.modulation.bend.value, bend_points)

    if adornment.fretting.modulation.trill is not None:
        # trill fret + duration of the trill
        guitarpro.models.TrillEffect(
            adornment.fretting.modulation.trill.fret,
            NotatedDuration_to_gp5_Duration(
                adornment.fretting.modulation.trill.notated_duration))

    if adornment.fretting.modulation.slide is not None:
        if adornment.fretting.modulation.slide.outto == 'slide_shift_to':
            note.effect.slides.append(guitarpro.models.SlideType.shiftSlideTo)
        if adornment.fretting.modulation.slide.outto == 'slide_out_below':
            note.effect.slides.append(guitarpro.models.SlideType.outDownwards)
        if adornment.fretting.modulation.slide.outto == 'slide_out_above':
            note.effect.slides.append(guitarpro.models.SlideType.outUpwards)
        if adornment.fretting.modulation.slide.outto == 'slide_legato':
            note.effect.slides.append(guitarpro.models.SlideType.legatoSlideTo)
        if adornment.fretting.modulation.slide.into == 'slide_from_above':
            note.effect.slides.append(guitarpro.models.SlideType.intoFromAbove)
        if adornment.fretting.modulation.slide.into == 'slide_from_below':
            note.effect.slides.append(guitarpro.models.SlideType.intoFromBelow)

    note.effect.vibrato = adornment.fretting.modulation.vibrato

    return beat, note


def dynamic_to_gp5_note(api_note, beat, note):

    note.velocity = utilities.dynamic2dB[api_note.dynamic.value]

    if api_note.dynamic.cres_dim is not None:

        beat.text = guitarpro.models.BeatText(api_note.dynamic.cres_dim)

    return beat, note


def NotatedDuration_to_gp5_Duration(notated_duration):

    return guitarpro.models.Duration(
        value=notated_duration.value.denominator,
        isDotted=notated_duration.isDotted,
        isDoubleDotted=notated_duration.isDoubleDotted,
        tuplet=guitarpro.models.Tuplet(
            enters=notated_duration.tuplet.number_of_notes,
            times=notated_duration.tuplet.equal_to))
