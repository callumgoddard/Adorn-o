"""
Some fun facts....

    - Needs R 3.2.1 to run the rpy2 stuff.
    - matlab.engine will only run on python <= 3.7
    - SynPy has issues when I did a futurize test..
    but all of my code can be futurized. - so maybe want to
    look into having the packaged installed not as a folder
    in my system.

"""


import guitarpro

import glob
import csv
import json
import os

import cbr
import parser

from fractions import Fraction

matlab_engine = parser.API.audio_out.start_matlab()
matlab_engine = parser.API.audio_out.add_physical_files_to_path(matlab_engine)


def initial_setup(database_name,
                  weight_set='RD',
                  convert_to_json=False,
                  new_database=True):
    complexity_weights = [1, 1, -1, 1, 0, -1, 0, -1]
    difficulty_weights = [1, -1, 1, 0, 1, 0, -1, -1]

    database = cbr.Database(
        database_name, weight_set=weight_set, new_database=new_database)
    database.load()
    print(len(list(database.data.keys())))

    #database.add_entries_from_list_of_gp5_files(
    #    ['./gp5files/GradePieces/Grade8/Love Games-no-repeats.gp5'],
    #    convert_to_json=True,
    #   move_tabs=False,
    #    artist_and_title_from_file_name=True)

    files = glob.glob(database_name + "/gpfiles/ultimate_guitar/*.gp[3-5]")
    #files = ['./database/gpfiles/ultimate_guitar/Mr. Big - Anything For You (ver 2 by ha_asgag).gp5']

    database.add_entries_from_list_of_gp5_files(
        files,
        convert_to_json=convert_to_json,
        move_tabs=False,
        artist_and_title_from_file_name=True)

    database.add_entries_from_list_of_gp5_files(
        glob.glob(database_name + "/gpfiles/digthatbass/*.gp[3-5]"),
        move_tabs=False,
        convert_to_json=convert_to_json,
        artist_and_title_from_file_name=False)

    database.add_entries_from_list_of_gp5_files(
        glob.glob("./gp5files/GradePieces/*/*.gp[3-5]"),
        convert_to_json=convert_to_json,
        move_tabs=False,
        artist_and_title_from_file_name=False)

    database.add_entries_from_list_of_gp5_files(
        glob.glob("./gp5files/Listening-test-mono/*.gp[3-5]"),
        convert_to_json=convert_to_json,
        move_tabs=False,
        artist_and_title_from_file_name=False)

    database = cbr.Database(database_name)
    database.load()
    print('Database Size: ', len(list(database.data.keys())))

    with open(database_name + '/virtuosity_thresholds.csv', 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        csvwriter.writerow([
            'virtuosity_type', 'complexity_weight', 'difficulty_weight',
            'complexity', 'difficulty'
        ])

        for complexity_weight, difficulty_weight in zip(
                complexity_weights, difficulty_weights):
            for virtuosity_type in ['performance', 'musical']:
                thresh = database.virtuosity_threshold(
                    complexity_weight,
                    difficulty_weight,
                    virtuosity_type=virtuosity_type)
                print('complexity_weight:', complexity_weight,
                      'difficulty_weight:', difficulty_weight)
                print('complexity:', thresh.complexity)
                print('difficulty:', thresh.difficulty)
                csvwriter.writerow([
                    virtuosity_type, complexity_weight, difficulty_weight,
                    thresh.complexity, thresh.difficulty
                ])


def database_virtuosity_thresholds(
        database_name,
        weight_set='RD',
        complexity_weights=[1, 1, -1, 1, 0, -1, 0, -1],
        difficulty_weights=[1, -1, 1, 0, 1, 0, -1, -1]):

    database = cbr.Database(database_name, weight_set=weight_set)
    database.load()
    print('Database Size: ', len(list(database.data.keys())))

    with open(database_name + '/virtuosity_thresholds.csv', 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        csvwriter.writerow([
            'virtuosity_type', 'complexity_weight', 'difficulty_weight',
            'complexity', 'difficulty'
        ])

        for complexity_weight, difficulty_weight in zip(
                complexity_weights, difficulty_weights):
            for virtuosity_type in ['performance', 'musical']:
                thresh = database.virtuosity_threshold(
                    complexity_weight,
                    difficulty_weight,
                    virtuosity_type=virtuosity_type)
                print('complexity_weight:', complexity_weight,
                      'difficulty_weight:', difficulty_weight)
                print('complexity:', thresh.complexity)
                print('difficulty:', thresh.difficulty)
                csvwriter.writerow([
                    virtuosity_type, complexity_weight, difficulty_weight,
                    thresh.complexity, thresh.difficulty
                ])


def process_input_files(input_files,
                        song_titles,
                        database,
                        weight_set,
                        output_info_file_name='output_info_rd',
                        matlab_engine=matlab_engine):
    database = cbr.Database(database, weight_set=weight_set)

    output_info_header = [
        'file', 'output_file', 'weight_set', 'virtuosity_percentile',
        'similarity_threshold', 'complexity_weight', 'difficulty_weight'
    ]

    output_info = []

    for virtuosity in [0, 0.5, 1]:
        for complexity_weight, difficulty_weight in zip(
            [1, 1, -1, 1, 0, -1, 0, -1], [1, -1, 1, 0, 1, 0, -1, -1]):
            for file, song_title in zip(input_files, song_titles):

                similarity_threshold, virtuosity_percentile = cbr.virtuosity_theshold_mapping(
                    virtuosity)
                output_file, new_songs = cbr.run_virtuosity_thesh_action_reflection(
                    file,
                    database,
                    song_title=song_title,
                    complexity_weight=complexity_weight,
                    difficulty_weight=difficulty_weight,
                    artist_and_title_from_file_name=False,
                    gp5_wellformedness=True,
                    add_to_database=False,
                    similarity_threshold=similarity_threshold,
                    similarity_threshold_relax_increment=5,
                    similarity_threshold_limit=0,
                    virtuosity_percentile=virtuosity_percentile,
                    percentile_search_expand_range=10,
                    comprehensive_search=True,
                    fixed_virtuosity_threshold=None,
                    loops_without_improvement_limit=25,
                )
                output_info.append([
                    file, output_file, weight_set, virtuosity_percentile,
                    similarity_threshold, complexity_weight, difficulty_weight
                ])

                gp_file_output = output_file.split(database.save_folder +
                                                   '/output/')[-1]
                gp_file_output = gp_file_output.split('.')[0]

                with open(
                        database.save_folder + '/output/' + gp_file_output +
                        '.csv',
                        mode='w') as output_info_file:
                    output_info_file_write = csv.writer(output_info_file)
                    output_info_file_write.writerow(output_info_header)
                    output_info_file_write.writerow([
                        file, output_file, weight_set, virtuosity_percentile,
                        similarity_threshold, complexity_weight,
                        difficulty_weight
                    ])

                print('Physical model:')
                track = 0
                for new_song in new_songs:
                    for note in parser.API.calculate_functions.calculate_physical_model_note_structures(
                            new_song,
                            matlab_engine=matlab_engine,
                            calculated_tied_notes=False):
                        print(note)

                    parser.API.audio_out.api_to_audio(
                        new_song, database.save_folder + '/output/' +
                        gp_file_output[0:2] + '_' + str(virtuosity) + '_' +
                        str(similarity_threshold) + '_' +
                        str(virtuosity_percentile) + '_' +
                        str(complexity_weight) + '_' + str(difficulty_weight) +
                        '.wav', matlab_engine)
                    track += 1

    with open(
            database.save_folder + output_info_file_name + '.csv',
            mode='w') as output_info_file:
        output_info_file_write = csv.writer(output_info_file)
        output_info_file_write.writerow(output_info_header)
        for row in output_info:
            output_info_file_write.writerow(row)

    return output_info


def make_audio_files(database, json_files, matlab_engine=matlab_engine):

    for json_file in json_files:

        new_songs = database.load_json_file(json_file)
        gp_file_output = json_file.split(database.save_folder + '/output/')[-1]
        gp_file_output = gp_file_output.split('.')[0]

        virtuosity = ''
        complexity_weight = ''
        difficulty_weight = ''
        print('Physical model:')
        track = 0
        for new_song in new_songs:
            for note in parser.API.calculate_functions.calculate_physical_model_note_structures(
                    new_song,
                    matlab_engine=matlab_engine,
                    calculated_tied_notes=False):
                print(note)
            parser.API.audio_out.api_to_audio(
                new_song,
                database.save_folder + '/output/' + gp_file_output[0:2] + '_' +
                str(track) + str(virtuosity) + '_' + str(complexity_weight) +
                '_' + str(difficulty_weight) + '.wav', matlab_engine)
            track += 1


def render_original_inputs(json_files, database):

    for json_file in json_files:
        json_file.split('.json')[0]
        for new_song in database.load_json_file(json_file):
            parser.API.audio_out.api_to_audio(
                new_song,
                json_file.split('.json')[0] + '.wav', matlab_engine)

    return


def make_json_files(gp5_files, song_names):

    json_files = []
    for gp5_file, song_name in zip(gp5_files, song_names):
        gp5song = guitarpro.parse(gp5_file)
        api_song_data = parser.API.get_functions.get_song_data(gp5song)

        if song_name == 'SB':
            # need to adjust the grace notes in this...
            for measure in api_song_data[0].measures:
                for note in measure.notes:
                    if isinstance(note, parser.API.datatypes.AdornedNote):
                        if note.adornment.grace_note is not None:
                            measure.notes[measure.notes.index(
                                note
                            )] = parser.API.datatypes.AdornedNote(
                                note=note.note,
                                adornment=parser.API.datatypes.Adornment(
                                    fretting=note.adornment.fretting,
                                    plucking=note.adornment.plucking,
                                    ghost_note=note.adornment.ghost_note,
                                    grace_note=parser.API.datatypes.GraceNote(
                                        fret=note.adornment.grace_note.fret,
                                        duration=note.adornment.grace_note.
                                        duration,
                                        dynamic=note.adornment.grace_note.
                                        dynamic,
                                        dead_note=note.adornment.grace_note.
                                        dead_note,
                                        on_beat=note.adornment.grace_note.
                                        on_beat,
                                        transition='hammer')))

            for measure in api_song_data[0].measures:
                for note in measure.notes:
                    if isinstance(note, parser.API.datatypes.AdornedNote):
                        if note.adornment.grace_note is not None:
                            assert note.adornment.grace_note.transition == 'hammer'

        json_data, json_dict = parser.API.write_functions.api_to_json(
            api_song_data)

        json_file = str(song_name + ".json")

        with open(json_file, "w") as write_file:
            json.dump(
                json_dict,
                write_file,
                indent=4,
            )

        try:
            with open(json_file) as read_file:
                json_data = json.load(read_file)
            json_api_song_data = parser.API.get_functions.get_from_JSON(
                json_data)
        except:
            print("Unable to load %s" % json_file)
            continue

        assert json_api_song_data == api_song_data

        json_files += [json_file]

        # set adornemnts to default:
        for measure in api_song_data[0].measures:
            for note in measure.notes:
                if isinstance(note, parser.API.datatypes.AdornedNote):
                    default_fretting = None
                    default_plucking = 'finger'
                    if note.note.fret_number > 0:
                        default_fretting = 'fretting'

                    if note.adornment.plucking.technique == "tied":
                        default_plucking = "tied"

                    measure.notes[measure.notes.index(
                        note
                    )] = parser.API.datatypes.AdornedNote(
                        note=parser.API.update_functions.update_note(
                            note.note,
                            dynamic=parser.API.datatypes.Dynamic('mf', None)),
                        adornment=parser.API.datatypes.Adornment(
                            fretting=parser.API.datatypes.FrettingAdornment(
                                technique=default_fretting,
                                modification=parser.API.datatypes.
                                FrettingModification(
                                    type=None, let_ring=False),
                                accent=False,
                                modulation=parser.API.datatypes.Modulation(
                                    bend=None,
                                    vibrato=False,
                                    slide=None,
                                    trill=None)),
                            plucking=parser.API.datatypes.PluckingAdornment(
                                technique=default_plucking,
                                modification=parser.API.datatypes.
                                PluckingModification(
                                    palm_mute=False, artificial_harmonic=None),
                                accent=False),
                            ghost_note=False,
                            grace_note=None))

        json_data, json_dict = parser.API.write_functions.api_to_json(
            api_song_data)

        json_file = str(song_name + "_unadorned" + ".json")

        with open(json_file, "w") as write_file:
            json.dump(
                json_dict,
                write_file,
                indent=4,
            )

        try:
            with open(json_file) as read_file:
                json_data = json.load(read_file)
            json_api_song_data = parser.API.get_functions.get_from_JSON(
                json_data)
        except:
            print("Unable to load %s" % json_file)
            continue

        assert json_api_song_data == api_song_data

        json_files += [json_file]

    return json_files


#
"""
"43a3b629-a44f-4405-afb7-a16505d4716a"
"4863c6bf-0115-4e0b-90a9-998bb39f8ee7"
"""
"""
gp_song = guitarpro.parse(input_files[0])
api_tracks = parser.API.get_functions.get_song_data(gp_song)
input_song = api_tracks[0]

# then get the new candidate set for the similarity:
new_virtuosity = database.virtuosity_threshold(
    complexity_weight=1,
    difficulty_weight=1,
    measure=None,
    notes_in_measure=[],
    virtuosity_type='performance',
    virtuosity_percentile=99,
)

print(new_virtuosity)
print(new_virtuosity.pieces)

# this is initially the top pieces in the range from the
# virtuosity_percentile to the best piece:
no_of_ids = {}
for v_p in range(0, 100):
    pieces = cbr.run_module.pick_percentile_pieces(
        new_virtuosity, virtuosity_percentile=v_p, percentile_range=1)

    # get only the ids...
    initial_candidates = map(lambda p: p.id, pieces)

    candidate_set_ids = []
    for c_id in initial_candidates:
        for i in c_id:
            candidate_set_ids.append(i)
    print(len(candidate_set_ids))
    consolidated_ids_to_files = database.consolidate_multiple_entries_from_same_files(
        candidate_set_ids)

    batch_size = 10
    number_of_batches = int(len(consolidated_ids_to_files) / batch_size) + 1

    for batch in range(0, number_of_batches):
        consolidated_batch = consolidated_ids_to_files.keys()[(
            batch * batch_size):(batch * batch_size + batch_size)]

        print(len(consolidated_batch))

        candidate_set = []
        for file_location in consolidated_batch:

            print('loading:', file_location)
            candidate_set += database.retrieve_data_form_multiple_entries_from_same_files(
                file_location, consolidated_ids_to_files[file_location])

        print(len(candidate_set))
        cbr.reuse_module.reuse_measures(input_song.measures[0], candidate_set)

    no_of_ids[v_p] = len(candidate_set_ids)
    print("no. ids:", len(candidate_set_ids))


# full_set = database.retrieve_data_from_multiple_entries(database.data.keys())
# cbr.reuse_module.reuse_measures(input_song.measures[0], full_set)


consolidated_ids_to_files = database.consolidate_multiple_entries_from_same_files(
        database.data.keys())

batch_size = 10
number_of_batches = int(len(consolidated_ids_to_files) / batch_size) + 1

for batch in range(0, number_of_batches):
    consolidated_batch = consolidated_ids_to_files.keys()[(
        batch * batch_size):(batch * batch_size + batch_size)]

    print(len(consolidated_batch))

    candidate_set = []
    for file_location in consolidated_batch:

        candidate_set += database.retrieve_data_form_multiple_entries_from_same_files(
            file_location, consolidated_ids_to_files[file_location])

    print(len(candidate_set))
    print(consolidated_batch)
    cbr.reuse_module.reuse_measures(input_song.measures[0], candidate_set)


input_files = glob.glob("./gp5files/Listening-test-mono/*.gp[3-5]")

print(input_files)

for file in input_files[3:]:

    cbr.run_virtuosity_thesh_action_reflection(
        file,
        database,
        complexity_weight=1,
        difficulty_weight=1,
        artist_and_title_from_file_name=False,
        gp5_wellformedness=True,
        add_to_database=False,
        similarity_threshold=85,
        similarity_threshold_relax_increment=5,
        similarity_threshold_limit=0,
        virtuosity_percentile=99,
        percentile_search_expand_range=1,
        comprehensive_search=True,
        fixed_virtuosity_threshold=None,
        loops_without_improvement_limit=None,
        percentile_range=[0, 100]
        )
"""
"""
for file in input_files[1:2]:
    print(file)
    new_song = cbr.run_action_reflection(
        file,
        database,
        complexity_weight=1,
        difficulty_weight=1,
        artist_and_title_from_file_name=False,
        gp5_wellformedness=True,
        add_to_database=False,
        virtuosity_percentile=99,
        virtuosity_similarity_threshold=90,
        reflection_loop_limit=None,
        similarity_threshold_relax_increment=1,
        percentile_range_relax_increment=1,
        similarity_threshold_limit=0,
        percentile_limit=0,
        similarity_threshold=99,
        percentile_range=[99, 100],
        # method=50  # picking top 50, also: 'all', 'best' or another number.
    )

    print(new_song)


gp5song = guitarpro.parse(new_song)
api_songs = parser.API.get_functions.get_song_data(gp5song)
new_song_data = api_songs[0]

for measure in new_song_data.measures:
    print(database.virtuosity_threshold(
        complexity_weight=1,
        difficulty_weight=1,
        measure=measure,
        virtuosity_type='performance',
        virtuosity_percentile=99,
        similarity_threshold=90))
    # need the complexity scores per bar....


new_files = []
for gp5_file in gp5_input_files:

    for complexity_weight, difficulty_weight in zip(complexity_weights,
                                                    difficulty_weights):
        new_song = cbr.run(
            gp5_file,
            'database',
            complexity_weight,
            difficulty_weight,
            retrieval_method,
            similarity_threshold,
            artist_and_title_from_file_name=True,
            gp5_wellformedness=True)
        new_files.append(new_song)

print(new_files)

gp5song = guitarpro.parse('./test_cbr/output/Thinking-Out-Loud.gp5')
revised_tol = parser.API.get_functions.get_song_data(gp5song)
revised_tol = revised_tol[0]
gp5song = guitarpro.parse("./gp5files/Listening-test-mono/tol.gp5")
tol = parser.API.get_functions.get_song_data(gp5song)
tol = tol[0]

tol_complexity = parser.API.calculate_functions.calculate_playing_complexity(
    tol, by_bar=False, calculation_type='both', weight_set='RD')
revised_tol_complexity = parser.API.calculate_functions.calculate_playing_complexity(
    revised_tol,
    by_bar=False,
    calculation_type='both',
    weight_set='RD')

print(tol_complexity, revised_tol_complexity)
print(revised_tol_complexity.BGM/tol_complexity.BGM, revised_tol_complexity.EVC/tol_complexity.EVC)


gp5song = guitarpro.parse('./database/output/Thinking-Out-Loud.gp5')
tol = parser.API.get_functions.get_song_data(gp5song)
tol = tol[0]

tol_complexity = parser.API.calculate_functions.calculate_playing_complexity(
    tol, by_bar=True, calculation_type='both', weight_set='RD', raw_values=True)

print(tol_complexity)

gp5_file = "./gp5files/Listening-test-mono/tol.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)

# Physical model output:
#physical_model_notes = parser.API.calculate_functions.calculate_physical_model_note_structures(
#    api_song[0])


eng = matlab.engine.start_matlab()
p = eng.genpath('/Users/cg306/Documents/MATLAB')
eng.addpath(p)
out1 = eng.CreateNotesStructure_callum(73.4161919793519)
out2 = eng.CreateNotesStructure_callum()
print(out1, out2)
fs = 44100.00

#print(physical_model_notes[0])
# need note structure + string:
#synth = eng.WaveGuide_BassGuitar('BA', physical_model_notes[0], 3, fs)
synth = eng.WaveGuide_BassGuitar('BA', out1, 1, fs)

data2 = np.asarray(synth[0])

scipy.io.wavfile.write('tes_note_1.wav', fs, data2)
out1, string = parser.API.calculate_functions.calculate_CreateNotesStructure_callum(api_song[0].measures[0].notes[0], api_song[0].measures[0].meta_data.tempo)
print(out1, string)
synth = eng.WaveGuide_BassGuitar('BA', out1, string, fs)
print(synth)
data2 = np.asarray(synth[0])

scipy.io.wavfile.write('note_test.wav', fs, data2)

print(eng.CalcFretPositions(100)[0][-1])
"""

if __name__ == "__main__":

    #print(os.getcwd())

    database_name = '../virtuobass/database'
    weight_set = 'RD'
    """
    initial_setup(
        database_name,
        weight_set=weight_set,
        convert_to_json=True,
        new_database=True)
    """
    database = cbr.Database(database_name, weight_set=weight_set)
    database.load()
    """
    unloadables = []
    for file in glob.glob('./database/json/*.json'):
        data = database.load_file(file)
        if not data:
            unloadables.append(file)
        else:
            print("data loaded ok!")

    measures = database.retrieve_data_from_multiple_entries(
        database.data.keys())
    assert len(measures) == len(database.data.keys())

    input_json = make_json_files(
        gp5_files=[
            database_name + '/input/validation_study_pieces/selected/FS.gp5',
            database_name + '/input/validation_study_pieces/selected/JB.gp5',
            database_name + '/input/validation_study_pieces/selected/CV.gp5',
            database_name + '/input/validation_study_pieces/selected/SB.gp5',
            database_name + '/input/validation_study_pieces/selected/TC.gp5',
            database_name + '/input/validation_study_pieces/selected/IM.gp5',
            database_name + '/input/validation_study_pieces/selected/VP.gp5',
            database_name + '/input/validation_study_pieces/selected/WP.gp5',
        ],
        song_names=['FS', 'JB', 'CV', 'SB', 'TC', 'IM', 'VP', 'WP'])

    render_original_inputs(input_json,
                           cbr.Database(database_name, weight_set=weight_set))

    #render_original_inputs([database_name +"/output/WP228a342e.json"],
    #                       cbr.Database(database_name, weight_set=weight_set))

    #assert False

    process_input_files(
        input_files=[
            database_name + '/input/validation_study_pieces/selected/FS.gp5',
            database_name + '/input/validation_study_pieces/selected/JB.gp5',
            database_name + '/input/validation_study_pieces/selected/CV.gp5',
            database_name + '/input/validation_study_pieces/selected/SB.gp5',
            database_name + '/input/validation_study_pieces/selected/TC.gp5',
            database_name + '/input/validation_study_pieces/selected/IM.gp5',
            database_name + '/input/validation_study_pieces/selected/VP.gp5',
            database_name + '/input/validation_study_pieces/selected/WP.gp5',
        ],
        song_titles=['FS', 'JB', 'CV', 'SB', 'TC', 'IM','VP', 'WP'
        ],
        database=database_name,
        weight_set=weight_set,
        output_info_file_name='output_info_rd',
        matlab_engine=matlab_engine)

    #render_original_inputs(["./database/output/JB97b0e750.json"],
    #                       cbr.Database(database_name, weight_set=weight_set))
    """

    #database_virtuosity_thresholds(database_name, weight_set)

    input_json = make_json_files(
        gp5_files=[
            database_name + '/input/single_note.gp5',
        ],
        song_names=['practice'])

    render_original_inputs(input_json,
                           cbr.Database(database_name, weight_set=weight_set))
