from __future__ import division, print_function, absolute_import

import json
# 3rd party imports
import guitarpro

import cbr
import parser

database = cbr.Database('test_retrieval', True)

database.add_entries_from_list_of_gp5_files(
    [
        "./gp5files/Listening-test-mono/c.gp5",
        "./gp5files/Listening-test-mono/r.gp5",
        "./gp5files/Listening-test-mono/h-official.gp5",
        "./gp5files/Listening-test-mono/tol.gp5",
        "./gp5files/Listening-test-mono/sd.gp5",
        "./gp5files/Listening-test-mono/s.gp5",
        "./gp5files/Listening-test-mono/wdytiw.gp5"
    ],
    convert_to_json=True,
    move_tabs=False,
    artist_and_title_from_file_name=False)

# Read in the file:
gp5_file = "./gp5files/Listening-test-mono/tol.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song = parser.API.get_functions.get_song_data(gp5song)

test_song = api_song[0]

database.load()

c_set = database.find_most_similar(
    test_song.measures[0],
    complexity_weight=1,
    difficulty_weight=1,
    similarity_threshold=100)
print(c_set)
assert len(c_set) == 1

c_set = database.find_most_similar(
    test_song.measures[0],
    complexity_weight=1,
    difficulty_weight=1,
    similarity_threshold=0,
    percentile_range=[75, 100])
assert len(c_set) == 6

candidate_test_set = database.data.keys()

sorted_test_set_1 = [
    cbr.candidate(5, 5, "id1"),
    cbr.candidate(5, 5, "id2"),
    cbr.candidate(4, 5, "id3"),
    cbr.candidate(4, 4, "id4"),
    cbr.candidate(3, 3, "id5")
]
consolidated_test = cbr.consolidate_same_complexity_difficulty(
    sorted_test_set_1)
assert consolidated_test == [
    cbr.candidate(complexity=5, difficulty=5, id=['id1', 'id2']),
    cbr.candidate(complexity=4, difficulty=5, id=['id3']),
    cbr.candidate(complexity=4, difficulty=4, id=['id4']),
    cbr.candidate(complexity=3, difficulty=3, id=['id5'])
]

sorted_test_set_2 = [
    cbr.candidate(5, 5, "id1"),
    cbr.candidate(4, 4, "id2"),
    cbr.candidate(3, 3, "id3"),
    cbr.candidate(2, 2, "id4"),
    cbr.candidate(1, 1, "id5")
]

for x, ans1, ans2 in zip(
        range(0, 5),
    [['id1', 'id2'], ['id1', 'id2'], ['id1', 'id2', 'id3'],
     ['id1', 'id2', 'id3', 'id4'], ['id1', 'id2', 'id3', 'id4', 'id5'
                                    ], ['id1', 'id2', 'id3', 'id4', 'id5']],
    [['id1'], ['id1'], ['id1', 'id2'], ['id1', 'id2', 'id3'],
     ['id1', 'id2', 'id3', 'id4'], ['id1', 'id2', 'id3', 'id4', 'id5']]):

    print(cbr.select_top_n_consolidated(consolidated_test, x))

    assert cbr.select_top_n_consolidated(consolidated_test, x) == ans1

    assert cbr.pick_top_candidate_ids(sorted_test_set_2, x) == ans2

for complexity_weight, difficulty_weight in [[1, 1], [0, 0], [-1, -1], [1, -1],
                                             [-1, 1], [1, 0], [0, 1]]:

    sorted_candidate_test_set = database.sort_candidate_set(
        candidate_test_set, complexity_weight, difficulty_weight)

    for sorted_c1, sorted_c2 in zip(sorted_candidate_test_set[::],
                                    sorted_candidate_test_set[1::]):
        heuristic = parser.API.calculate_functions.calculate_heuristic(
            float(sorted_c1.complexity), float(sorted_c2.complexity),
            float(sorted_c1.difficulty), float(sorted_c2.difficulty),
            complexity_weight, difficulty_weight)
        assert heuristic >= 0

    # then test cbr.pick_top_candidate_ids()
    for n in range(0, len(sorted_candidate_test_set)):
        print(sorted_candidate_test_set)
        top_n = cbr.pick_top_candidate_ids(sorted_candidate_test_set, n)

        print(top_n)
        print(complexity_weight, difficulty_weight)
        if n == 0:
            assert len(top_n) == 1
        else:
            assert len(top_n) == n
        count = 0
        for top_c in top_n:
            assert top_c == sorted_candidate_test_set[count].id
            count += 1

        # manually load the data, check its in the list:
        retrieved_measures = cbr.retrieve_candidate_data(top_n, database)

        for r_m in retrieved_measures:
            c_id = r_m.id
            c_file = database.data[c_id][database.header.index("file.location")
                                         - 1]

            with open(database.save_folder + "/" + c_file, "r") as read_file:
                c_json_song = json.load(read_file)

            #c_gpsong = guitarpro.parse(c_gpfile)
            c_api_song = parser.API.get_functions.get_from_JSON(c_json_song)

            track_col = database.header.index("track") - 1
            measure_col = database.header.index("measure.number") - 1

            track_num = int(database.data[c_id][track_col])
            measure_num = int(database.data[c_id][measure_col])
            c_measure_data = c_api_song[track_num].measures[measure_num - 1]

            tied_notes = parser.API.calculate_functions.calculate_tied_note_durations(
                c_api_song[track_num])
            notes_in_measures = parser.API.calculate_functions.calculate_bars_from_note_list(
                tied_notes, c_api_song[track_num])

            c_measure_data = parser.API.datatypes.Measure(
                meta_data=c_measure_data.meta_data,
                start_time=c_measure_data.start_time,
                notes=notes_in_measures[measure_num - 1])
            assert r_m.measure == c_measure_data

    parser.API.calculate_functions.calculate_tied_note_durations(
        test_song.measures[0])
    retrieved_measures = cbr.retrieval(
        test_song.measures[0],
        parser.API.calculate_functions.calculate_tied_note_durations(
            test_song.measures[0]),
        database,
        complexity_weight,
        difficulty_weight,
        similarity_threshold=100)
    print(retrieved_measures[0].measure)
    assert len(retrieved_measures) == 1
    assert retrieved_measures[0].measure == test_song.measures[0]

    retrieved_measures = cbr.retrieval(
        test_song.measures[0],
        parser.API.calculate_functions.calculate_tied_note_durations(
            test_song.measures[0]),
        database,
        complexity_weight,
        difficulty_weight,
        similarity_threshold=0,
        method=2)

    assert len(retrieved_measures) == 2
    if complexity_weight != 0 and difficulty_weight != 0:
        print(map(lambda rm: rm.id, retrieved_measures))
        print(map(lambda sc: sc.id, sorted_candidate_test_set[0:2]))

        assert map(lambda rm: rm.id, retrieved_measures) == map(
            lambda sc: sc.id, sorted_candidate_test_set[0:2])

    retrieved_measures = cbr.retrieval(
        test_song.measures[0],
        parser.API.calculate_functions.calculate_tied_note_durations(
            test_song.measures[0]),
        database,
        complexity_weight,
        difficulty_weight,
        similarity_threshold=0,
        method='best')
    assert len(retrieved_measures) == 1
    if complexity_weight != 0 and difficulty_weight != 0:
        assert retrieved_measures[0].id == sorted_candidate_test_set[0].id

database.load()
database.data.keys()
#database.retrieve_entry_data()
