'''
Interface for SynPy:
https://code.soundsoftware.ac.uk/projects/syncopation-dataset
'''

# Standard library imports
import csv
import os.path

# 3rd party imports
import synpy
import synpy.PRS as PRS
import synpy.KTH as KTH
import synpy.LHL as LHL
import synpy.SG as SG
import synpy.TMC as TMC
import synpy.TOB as TOB
import synpy.WNBD as WNBD

import pandas as pd


features_list_all = [
    'source', 'model_name', 'syncopation_by_bar', 'number_of_bars',
    'summed_syncopation', 'mean_syncopation_per_bar', 'bars_with_valid_output',
    'bars_without_valid_output', 'number_of_bars_not_measured'
]

models_all = ['PRS', 'KTH', 'LHL', 'SG', 'TMC', 'TOB', 'WNBD']

txt2models = {
    'PRS': PRS,
    'KTH': KTH,
    'LHL': LHL,
    'SG': SG,
    'TMC': TMC,
    'TOB': TOB,
    'WNBD': WNBD
}

# to parse a json file:
# http://python-guide-pt-br.readthedocs.io/en/latest/scenarios/json/


def compute_features(file, features=['mean_syncopation_per_bar'], models=models_all, bar=None):

    synpy_bars = None

    syncopation_features = []
    file_name = os.path.split(file)[1].split('.')[0]

    if bar is not None:
        synpy_bars = synpy.rhythm_parser.read_rhythm(file)

        syncopation_features.append(file_name+"_bar_"+str(bar))

        for m in models:
            try:
                s = synpy.calculate_syncopation(txt2models.get(m), synpy_bars[bar-1])
            except:
                "Error cannot analyse %i of %s file" % (bar, file_name)
                s = {}
                for feature in features:
                    s[feature] = None

            for f in features:
                syncopation_features.append(s.get(f))

    else:

        syncopation_features = []
        syncopation_features.append(file_name)

        for m in models:
            try:
                s = synpy.calculate_syncopation(txt2models.get(m), file)
            except:
                "Error cannot analyse skipping.. a bar of %s" % file_name
                s = {}
                for feature in features:
                    s[feature] = None

            for f in features:
                syncopation_features.append(s.get(f))

    return syncopation_features


def make_feature_table(RHY_files,
                       output='synpy_features.csv',
                       features=['mean_syncopation_per_bar'],
                       models=models_all,
                       save=True,
                       byBar=True):

    header = []
    header.append('file.id')

    for m in models:
        for f in features:
            col_title = m + '.' + f
            header.append(col_title)

    data = []
    data.append(header)

    # Loop through the file list
    if type(RHY_files) == list:
        for f in RHY_files:
            if type(f) == list:
                rhy_file = f[0]
                bars = f[1]
                if byBar:
                    for bar in bars:
                        synpy_data = compute_features(rhy_file, features, models, bar)
                        data.append(synpy_data)

            else:
                data.append(compute_features(f, features, models))

    elif type(RHY_files) == str or type(RHY_files) == unicode:
        if byBar:
            bars = synpy.rhythm_parser.read_rhythm(RHY_files)
            bar_count = 0
            for bar in bars:
                bar_count += 1
                synpy_data = compute_features(RHY_files, features, models, barRange=[bar_count-1, bar_count])
                # update the file id to include bar numbers:
                #synpy_data[0] = synpy_data[0]+"_bar_" + str(bar_count)
                data.append(synpy_data)

        else:
            data.append(compute_features(RHY_files, features, models))

    # make the csv file a data frame
    df = pd.DataFrame(data[1:], columns=data[0])

    if save is True:
        with open(output, 'wb') as csvfile:
            synpywriter = csv.writer(csvfile, delimiter=',')
            for row in data:
                synpywriter.writerow(row)
    # df.to_csv('test.csv')

    return df
