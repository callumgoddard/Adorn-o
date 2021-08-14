import pandas
import glob
import csv
from fractions import Fraction
import guitarpro
from bisect import bisect_left
from math import log, e

import pkg_resources

# Set the folder with the musiplectics score data
musiplectics_folder = pkg_resources.resource_filename(__name__, 'musiplectics')

musiplectic_score_file_names = {
    'intervals': '/interval.musiplectics.score.csv',
    'intervals_total': '/interval.total.musiplectics.score.csv'
}

technique_col = 0
musiplectic_score_col = 1


def make_complexity_score_dict(input_file):
    '''
    Read in complexity value from the indicated value file and
    make a dictionary of them, returning the dictionary.
    This can be used when no special parsing is required to setup the dictionary keys.
    '''
    values = {}
    with open(input_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            values[rows[technique_col]] = float(rows[musiplectic_score_col])
    return values


def fret_position_weights(musiplectics_folder=musiplectics_folder,
                          use_geometric_mean=True,
                          use_total_playing_time=False,
                          log_scale_values=True):
    '''
    Create an dictionary where the keys are fret postiions (in fret ranges)
    and the values are the playing complexity weight for the ranges.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/fretboard.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/fretboard.total.musiplectics.score.csv'
    else:

        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/fretboard.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/fretboard.musiplectics.relative.total.csv'

    # Return a dict of the note complexity values
    values = {}
    with open(value_file, mode='r') as value_file:
        reader = csv.reader(value_file)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            if rows[technique_col] == 'X18th.fret.and.beyond.' or rows[technique_col] == '18th.fret.and.beyond.':
                key = '18+'
            if rows[technique_col] == 'Between.5th.and.11th.':
                key = '5-11'
            if rows[technique_col] == 'Between.12th.and.17th.':
                key = '12-17'
            if rows[technique_col] == 'Open.string.up.to.4th.fret.':
                key = '0-4'
            values[key] = float(rows[musiplectic_score_col])

    # if log scale is true, scale the values:
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    return values


def interval_weights(musiplectics_folder=musiplectics_folder,
                     use_geometric_mean=True,
                     use_total_playing_time=False,
                     log_scale_values=True):
    '''
    Create an dictionary where the keys are interval distances (in semitones)
    and the values are the playing complexity weight for the intervals

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Make a dictionary for the values
    interval_values = {}

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/interval.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/interval.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/interval.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/interval.musiplectics.relative.total.csv'

    # Read in complexity values for intervals  from the relevant musiplectics csv file:
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            # try catch statements to parse the values for semitone ammounts
            # but due to some spelling errors require a few passes.
            try:

                interval = rows[technique_col].split('.').index('semitones') - 1

                interval_values[int(
                    rows[technique_col].split('.')[interval])] = float(
                        rows[musiplectic_score_col])

            except ValueError:

                try:
                    interval = rows[technique_col].split('.').index(
                        'Semitones') - 1
                    interval_values[int(
                        rows[technique_col].split('.')[interval])] = float(
                            rows[musiplectic_score_col])
                except ValueError:
                    try:
                        interval = rows[technique_col].split('.').index(
                            'semitone') - 1
                        interval_values[int(
                            rows[technique_col].split('.')[interval])] = float(
                                rows[musiplectic_score_col])
                    except ValueError:
                        print("Not an interval")

    # if log scale is true, scale the values:
    values = interval_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    interval_values = values
    return interval_values


def dynamic_weights(musiplectics_folder=musiplectics_folder,
                    use_geometric_mean=True,
                    use_total_playing_time=False,
                    log_scale_values=True):
    '''
    Create an dictionary where the keys are idynamics
    and the values are the playing complexity weight.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/dynamic.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/dynamic.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        value_file = musiplectics_folder + '/dynamic.musiplectics.relative.csv'

    # Make a dictionary for the values
    dynamic_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            dynamic = rows[technique_col].split('.')[0]
            if dynamic == 'No':
                dynamic = 'none'
            dynamic_values[dynamic] = float(rows[musiplectic_score_col])

    # Add missing dynamic values:
    dynamic_values['fff'] = dynamic_values.get('ff')
    dynamic_values['ppp'] = dynamic_values.get('pp')
    if use_geometric_mean:
        if not use_total_playing_time:
            dynamic_values['fff'] = 1.33
            dynamic_values['ppp'] = 1.55
        else:
            dynamic_values['fff'] = 2.85
            dynamic_values['ppp'] = 4.42
    else:
        if not use_total_playing_time:
            dynamic_values['fff'] = 1.11
            dynamic_values['ppp'] = 1.2
        else:
            dynamic_values['fff'] = 3.19
            dynamic_values['ppp'] = 3.91

    # if log scale is true, scale the values:
    values = dynamic_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    dynamic_values = values

    return dynamic_values


def key_sig_weights(musiplectics_folder=musiplectics_folder,
                    use_geometric_mean=True,
                    use_total_playing_time=False,
                    log_scale_values=True):
    '''
    Create an dictionary where the keys are key signatures
    and the values are the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/key.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/key.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/key.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/key.musiplectics.relative.total.csv'

    # Make a dictionary for the values
    keysig_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            if rows[technique_col] == "C.Major...A.Minor...0.Sharps.Flats.":
                major_keysig = "CMajor"
                minor_keysig = "AMinor"
            elif rows[technique_col] == "F.Major...D.Minor...1.Flat.":
                major_keysig = "FMajor"
                minor_keysig = "DMinor"
            elif rows[technique_col] == "Bb.Major...G.Minor...2.Flats.":
                major_keysig = "BMajorFlat"
                minor_keysig = "GMinor"
            elif rows[technique_col] == "Eb.Major...C.Minor...3.Flats.":
                major_keysig = "EMajorFlat"
                minor_keysig = "CMinor"
            elif rows[technique_col] == "Ab.Major...F.Minor...4.Flats.":
                major_keysig = "AMajorFlat"
                minor_keysig = "FMinor"
            elif rows[technique_col] == "Db.Major...Bb.Minor...5.Flats.":
                major_keysig = "DMajorFlat"
                minor_keysig = "BMinorFlat"
            elif rows[technique_col] == "Gb.Major...Eb.Minor...6.Flats.":
                major_keysig = "GMajorFlat"
                minor_keysig = "EMinorFlat"
            elif rows[technique_col] == "Cb.Major...Ab.Minor...7.Flats.":
                major_keysig = "CMajorFlat"
                minor_keysig = "AMinorFlat"
            elif rows[technique_col] == "G.Major...E.Minor...1.Sharp.":
                major_keysig = "GMajor"
                minor_keysig = "EMinor"
            elif rows[technique_col] == "D.Major...B.Minor...2.Sharps.":
                major_keysig = "DMajor"
                minor_keysig = "BMinor"
            elif rows[technique_col] == "A.Major...F..Minor...3.Sharps.":
                major_keysig = "AMajor"
                minor_keysig = "FMinorSharp"
            elif rows[technique_col] == "E.Major...C..Minor...4.Sharps.":
                major_keysig = "EMajor"
                minor_keysig = "CMinorSharp"
            elif rows[technique_col] == "B.Major...G..Minor...5.Sharps.":
                major_keysig = "BMajor"
                minor_keysig = "GMinorSharp"
            elif rows[technique_col] == "F..Major...D..Minor...6.Sharps.":
                major_keysig = "FMajorSharp"
                minor_keysig = "DMinorSharp"
            elif rows[technique_col] == "C..Major...A..Minor...7.Sharps.":
                major_keysig = "CMajorSharp"
                minor_keysig = "AMinorSharp"

            keysig_values["KeySignature." + major_keysig] = float(
                rows[musiplectic_score_col])
            keysig_values["KeySignature." + minor_keysig] = float(
                rows[musiplectic_score_col])

    # if log scale is true, scale the values:
    values = keysig_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    keysig_values = values

    return keysig_values


def articulation_weights(musiplectics_folder=musiplectics_folder,
                         use_geometric_mean=True,
                         use_total_playing_time=False,
                         log_scale_values=True):
    '''
    Create an dictionary where the keys are articulation techniques
    and the values are the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/articulations.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/articulations.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/articulations.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/articulations.musiplectics.relative.total.csv'

    articulation_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            articulation_type = rows[technique_col].split('.')[0].lower()
            if articulation_type == "no":
                articulation_type = None
            articulation_values[articulation_type] = float(
                rows[musiplectic_score_col])

    # if log scale is true, scale the values:
    values = articulation_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    articulation_values = values

    return articulation_values


def duration_weights(musiplectics_folder=musiplectics_folder,
                     use_geometric_mean=True,
                     use_total_playing_time=False,
                     log_scale_values=True):
    '''
    Create an dictionary where the keys are duration numbers
    (in clicks per minute) and the values are
    the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/tempo.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/tempo.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/tempo.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/tempo.musiplectics.relative.total.csv'

    duration_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            # Convert tempo value into a real_time duration:
            click_rate = float(rows[technique_col].split('.')[5])
            click_rate_rt = 60000 / click_rate

            duration_values[click_rate_rt] = float(rows[musiplectic_score_col])

    # if log scale is true, scale the values:
    values = duration_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    duration_values = values

    return duration_values


def expression_weights(musiplectics_folder=musiplectics_folder,
                       use_geometric_mean=True,
                       use_total_playing_time=False,
                       log_scale_values=True):
    '''
    Create an dictionary where the keys are expression techniques
    and the values are the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/expression.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/expression.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/expression.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/expression.musiplectics.relative.total.csv'

    expression_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            elif rows[technique_col] == "Applying.no.expression.":
                expression_type = 'none'
            elif rows[technique_col] == "Bending.a.note.by.a.quarter.tone.":
                expression_type = 'quater_bend'
            elif rows[technique_col] == "Bend.a.note.by.a.semitone.":
                expression_type = 'half_bend'
            elif rows[technique_col] == "Bending.a.note.by.whole.tone.":
                expression_type = 'whole_bend'
            elif rows[technique_col] == "Fast.Vibrato.":
                expression_type = 'fast-vibrato'
            elif rows[technique_col] == "Slow.Vibrato.":
                expression_type = 'slow-vibrato'
            elif rows[technique_col] == "Trill.using.hammer.on.pull.offs.":
                expression_type = 'trill'
            elif rows[technique_col] == "Trill.by.sliding.between.notes.":
                expression_type = 'trill-slide'
            elif rows[technique_col] == "Slide.":
                expression_type = 'slide'

            expression_values[expression_type] = float(
                rows[musiplectic_score_col])
    # Average vibrato values as can't determine between fast and slow vibrato:
    expression_values['vibrato'] = (expression_values['fast-vibrato'] +
                                    expression_values['slow-vibrato']) / 2

    # if log scale is true, scale the values:
    values = expression_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    expression_values = values

    return expression_values


def shifting_weights(musiplectics_folder=musiplectics_folder,
                     use_geometric_mean=True,
                     use_total_playing_time=False,
                     log_scale_values=True,
                     add_no_shift=True):
    '''
    Create an dictionary where the keys are shifting distances
    and the values are the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/shifting.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/shifting.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/shifting.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/shifting.musiplectics.relative.total.csv'

    shifting_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            if rows[technique_col] != 'fret.distances...More.than.12.frets.':

                shift_distance = rows[technique_col].split('.')[
                    len(rows[technique_col].split('.')) - 2]
                shifting_values[shift_distance] = float(
                    rows[musiplectic_score_col])
            else:
                shifting_values['13+'] = float(rows[musiplectic_score_col])

    if add_no_shift:
        if use_geometric_mean:
            # add the value for no shift:
            if not use_total_playing_time:
                shifting_values['0'] = 0.997  # 0.942 = expo
            else:
                shifting_values['0'] = 0.961

        else:
            if not use_total_playing_time:
                shifting_values['0'] = 0.942
            else:
                shifting_values['0'] = 0.961

        # rescale the other shifting values to make no shift = 1:
        for key in list(shifting_values.keys()):
            shifting_values[
                key] = shifting_values.get(key) / shifting_values.get('0')

    # if log scale is true, scale the values:
    values = shifting_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    shifting_values = values

    return shifting_values


def technique_weights(musiplectics_folder=musiplectics_folder,
                      use_geometric_mean=True,
                      use_total_playing_time=False,
                      log_scale_values=True,
                      add_no_shift=True):
    '''
    Create an dictionary where the keys are techniques
    and the values are the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/technique.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/technique.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/technique.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/technique.musiplectics.relative.total.csv'

    technique_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            if rows[technique_col] == "X1.Finger.Pluck." or rows[technique_col] == "1.Finger.Pluck.":
                technique = '1_finger_pluck'
            if rows[technique_col] == "X2.Finger.Plucking." or rows[technique_col] == "2.Finger.Plucking.":
                technique = '2_finger_pluck'
            if rows[technique_col] == "X3.Finger.Plucking." or rows[technique_col] == "3.Finger.Plucking.":
                technique = '3_finger_pluck'
            if rows[technique_col] == "Raking.":
                technique = 'ranking'
            if rows[technique_col] == "Thumb.Pluck.":
                technique = 'thumb_pluck'
            if rows[technique_col] == "Using.a.Pick.":
                technique = 'pick'
            if rows[technique_col] == "Slapping.":
                technique = 'slap'
            if rows[technique_col] == "Popping.":
                technique = 'pop'
            if rows[technique_col] == "Double.Thumb...up.stroke.":
                technique = 'double_thumb_downstroke'
            if rows[technique_col] == "Double.Thumb...down.stroke.":
                technique = 'double_thumb_upstroke'
            if rows[technique_col] == "Palm.muting...thumb.pluck.":
                technique = 'palm_mute_thumb_pluck'
            if rows[technique_col] == "Palm.muting...using.a.pick.":
                technique = 'palm_mute_pick'
            if rows[technique_col] == "Palm.muting...finger.pluck.":
                technique = 'palm_mute_pluck'
            if rows[technique_col] == "Tapping....with.plucking.hand.":
                technique = 'tap'
            if rows[technique_col] == "Two.Handed.Tapping.":
                technique = 'two_handed_tap'
            if rows[technique_col] == "Fretting.hand..left.hand..slap.":
                technique = 'fretting_slap'
            if rows[technique_col] == "Hammer.on.":
                technique = 'hammer_on'
            if rows[technique_col] == "Pull.off.":
                technique = 'pull_off'
            if rows[technique_col] == "Harmonic.":
                technique = "natural_harmonic"
            if rows[technique_col] == "Dead.note...plucked.picked.":
                technique = "dead_note_pluck_pick"
            if rows[technique_col] == "Dead.note...slapped.":
                technique = 'dead_note_slap'
            if rows[technique_col] == "Dead.note...popped.":
                technique = 'dead_note_pop'
            if rows[technique_col] == "Artificial.Harmonic.":
                technique = "artificial_harmonic"
            if rows[technique_col] == "Double.Stops.":
                technique = 'double_stop'
            if rows[technique_col] == "Chords...3.note.voicing.":
                technique = '3_note_chord'
            if rows[technique_col] == "Chords...4.note.voicing.":
                technique = '4_note_chord'

            technique_values[technique] = float(rows[musiplectic_score_col])

    # if log scale is true, scale the values:
    values = technique_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values
            values[key] = log((values.get(key) + 1), 2)

    technique_values = values

    return technique_values


def tempo_weights(musiplectics_folder=musiplectics_folder,
                  use_geometric_mean=True,
                  use_total_playing_time=False,
                  log_scale_values=True,
                  add_no_shift=True):
    '''
    Create an dictionary where the keys are tempos (in bpm)
    and the values are the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/tempo.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/tempo.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/tempo.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/tempo.musiplectics.relative.total.csv'

    tempo_values = {}
    tempo_beat_dur_rt = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue

            # split the tempo value list and take the 2nd from last value which is just the bmp number.
            tempo = rows[technique_col].split('.')[
                len(rows[technique_col].split('.')) - 2]
            # calculate how long in seconds a beat is at this tempo:
            beat_dur_seconds = float(60) / float(tempo)

            # Add tempo + complexity to dictionary
            # and add the beat dur in [r]eal[t]ime to a separate dictionary.
            tempo_values[int(tempo)] = float(rows[musiplectic_score_col])
            tempo_beat_dur_rt[beat_dur_seconds] = float(
                rows[musiplectic_score_col])

    # if log scale is true, scale the values:
    values = tempo_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    tempo_values = values

    # if log scale is true, scale the values:
    values = tempo_beat_dur_rt
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    tempo_beat_dur_rt = values

    return tempo_values, tempo_beat_dur_rt


def time_sig_weights(musiplectics_folder=musiplectics_folder,
                     use_geometric_mean=True,
                     use_total_playing_time=False,
                     log_scale_values=True,
                     add_no_shift=True):
    '''
    Create an dictionary where the keys are time signatures
    and the values are the playing complexity weight for these.

    The type of complexity weights can be determined by the geometric
    mean probabilities or relative probabilites, indicated by the
    geometric_mean flag. When use_geometric_mean = True the
    geometric mean probabilities are used, when set to false the
    relative probabilites are used instead. Relative probabilities do not
    need to be log scaled.

    It is also possible to use the total_playing_time option to use
    the total_playing_time probabilities.
    Use this by setting use_total_playing_time = True.
    '''

    # Check if the geometric mean probs should be used or relative probs:
    if use_geometric_mean:
        # Deteriming if the total playing time file or average playing time calculations should be used:
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/time.sig.musiplectics.score.csv'
        else:
            value_file = musiplectics_folder + '/time.sig.total.musiplectics.score.csv'
    else:
        # set log scale to false is geometric mean = false:
        log_scale_values = False
        if not use_total_playing_time:
            value_file = musiplectics_folder + '/time.sig.musiplectics.relative.csv'
        else:
            value_file = musiplectics_folder + '/time.sig.musiplectics.relative.total.csv'

    timesig_values = {}
    with open(value_file, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            if rows[technique_col] == 'technique':
                continue
            split_row = rows[technique_col].split('.')
            numerator = split_row[len(split_row) - 3]
            denominator = split_row[len(split_row) - 2]
            timesig_values[str(numerator) + "/" + str(denominator)] = float(
                rows[musiplectic_score_col])
    # Add some additional complexity values:
    # '5/8 is missing: so take the average between 3/8 and 6/8'
    timesig_values['5/8'] = (timesig_values['3/8'] + timesig_values['6/8']) / 2

    # if log scale is true, scale the values:
    values = timesig_values
    if log_scale_values:
        for key in list(values.keys()):
            # log scale the values, and rest the '0' to be 1:
            values[key] = log((values.get(key) + 1), 2)

    timesig_values = values

    return timesig_values


def duration_complexity_polynomial(duration,
                                   use_geometric_mean=True,
                                   log_scale_values=True,
                                   use_total_playing_time=False):
    '''
    This is a function to calculate the duration complexity of a note
    based on a polynomial equations that was
    fitted to the initial click data. This allows for notes
    with a duration of less than 200ms to be modeled as well as
    giving more precise scores to values inbetween
    the click tracks that were assess in the study.
    '''

    # conver the duration into clicks per minute:
    clicks = 60000 / duration

    if use_geometric_mean:
        if not use_total_playing_time:

            duration_complexity = (
                9.51 - 0.141 * clicks + 0.000699 * pow(clicks, 2))

        else:

            duration_complexity = (
                14.8 - 0.224 * clicks + 0.00106 * pow(clicks, 2))

        if log_scale_values:
            return log((duration_complexity + 1), 2)
        else:
            return duration_complexity
    else:
        if not use_total_playing_time:
            duration_complexity = (
                1.6 - 0.0109 * clicks + 0.0000618 * pow(clicks, 2))
            return duration_complexity
        else:

            duration_complexity = (
                1.43 - 0.00738 * clicks + 0.0000399 * pow(clicks, 2))

            return duration_complexity


def shifting_complexity_function(shift_distance,
                                 log_scale_values=True,
                                 polynomial=True):
    '''
    Calculate the shifting complexity using an exponential
    fitted to the original musiplectics responce data.
    '''
    if polynomial:
        # polynomial R^2 = 0.997
        if log_scale_values:
            # Add 1 to start the values at 1.
            return 1 + log(
                1 - 3.82 * shift_distance + 4.22 * pow(shift_distance, 2) -
                1.65 * pow(shift_distance, 3) + 0.308 * pow(shift_distance, 4)
                - 0.0253 * pow(shift_distance, 5) +
                0.000758 * pow(shift_distance, 6), 10)
        else:
            return (
                1 - 3.82 * shift_distance + 4.22 * pow(shift_distance, 2) -
                1.65 * pow(shift_distance, 3) + 0.308 * pow(shift_distance, 4)
                - 0.0253 * pow(shift_distance, 5) +
                0.000758 * pow(shift_distance, 6))
    else:
        # these exponetial equations have an R^2 = 0.973
        if log_scale_values:
            # Add 1 to start the values at 1.
            return 1 + log(1.77 * pow(e, 0.295 * shift_distance) - 0.77, 10)
        else:
            return 1.77 * pow(e, 0.295 * shift_distance) - 0.77, 10
