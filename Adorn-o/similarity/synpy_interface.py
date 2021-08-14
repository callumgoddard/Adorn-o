import synpy
import synpy.PRS as PRS
import synpy.KTH as KTH
import synpy.LHL as LHL
import synpy.SG as SG
import synpy.TMC as TMC
import synpy.TOB as TOB
import synpy.WNBD as WNBD
import csv
import pandas as pd
from rpy2.robjects import r, pandas2ri
import os.path

pandas2ri.activate()

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


def compute_features(file, features=features_list_all, models=models_all):

    file_name = os.path.split(file)[1].split('.')[0]

    syncopation_features = []
    syncopation_features.append(file_name)

    print(file_name)
    for m in models:
        s = synpy.calculate_syncopation(txt2models.get(m), file)
        for f in features:
            syncopation_features.append(s.get(f))
    '''
  for m in models:
          s = synpy.calculate_syncopation(PRS, file)
          for f in features:
              syncopation_features.append(s.get(f))
      print header
    '''
    # synpy.calculate_syncopation(PRS, file, outfile=output_folder + file_name + '-PRS.json')
    # synpy.calculate_syncopation(PRS, file)

    # synpy.calculate_syncopation(KTH, file, outfile=output_folder + file_name + '-KTH.json')
    # synpy.calculate_syncopation(LHL, file, outfile=output_folder + file_name + '-LHL.json')
    # synpy.calculate_syncopation(SG, file, outfile=output_folder + file_name + '-SG.json')
    # synpy.calculate_syncopation(TMC, file, outfile=output_folder + file_name + '-TMC.json')
    # synpy.calculate_syncopation(TOB, file, outfile=output_folder + file_name + '-TOB.json')
    # synpy.calculate_syncopation(WNBD, file, outfile=output_folder + file_name + '-WNBD.json')

    return syncopation_features


def make_feature_table(RHY_files,
                       output='synpy_features.csv',
                       features=features_list_all,
                       models=models_all,
                       save=True):
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
            # print compute_features(f, features, models)
            data.append(compute_features(f, features, models))
    elif type(RHY_files) == str:
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


def main():
    file = 'out.rhy'
    file_name = file.split('.')[0]
    output_folder = '/examples/'

    print(output_folder + file_name + '-PRS.json')
    make_feature_table('out.rhy')

    # output of each funtion is a dictionary.
    # print synpy.calculate_syncopation(PRS, file).get('mean_syncopation_per_bar')

    # make a list of features - write it out to a csv file
    # merge that with fantastic...


if __name__ == "__main__":
    main()
