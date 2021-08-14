

import os
import glob
from collections import namedtuple

from math import floor, log10, ceil

# 3rd party imports
import guitarpro

from .. import cbr
from .. import parser

BestMeasure = namedtuple("BestMeasure",
                         ["measure", 'complexity', 'difficulty'])


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def run(gp5_file,
        database,
        song_title=None,
        complexity_weight=1,
        difficulty_weight=1,
        weight_set='RD',
        artist_and_title_from_file_name=False,
        gp5_wellformedness=True,
        add_to_database=True,
        **retrieval_parameters):
    """

    Parameters
    ---------
    gp5_file,
    database,
    complexity_weight=1,
    difficulty_weight=1,
    retrieval_method='all',
    similarity_threshold=100,
    artist_and_title_from_file_name=False,
    gp5_wellformedness=True



    """
    if isinstance(database, str):
        database = cbr.Database(database)
    else:
        assert isinstance(database,
                          cbr.Database), "database must be a database"

    # Read in the file:
    if song_title is None:
        song_title = gp5_file.split(".")[0]

    gp5song = guitarpro.parse(gp5_file)

    if gp5song.title != "":
        song_title = gp5song.title

    api_songs = parser.API.get_functions.get_song_data(gp5song)
    song = api_songs[0]

    new_songs = []
    for track in range(0, len(api_songs)):
        song = api_songs[track]
        # for song in api_songs:
        # Combine tied notes and sort the list back into bars:
        note_list = parser.API.calculate_functions.calculate_tied_note_durations(
            api_songs[track])
        notes_in_measure = parser.API.calculate_functions.calculate_bars_from_note_list(
            note_list, api_songs[track])

        new_measures = []
        for unadorned_measure in song.measures:
            measure_number = unadorned_measure.meta_data.number - 1

            if not database.valid_measure(unadorned_measure,
                                          notes_in_measure[measure_number]):
                # append the measure to keep continuity and continue:
                new_measures.append(unadorned_measure)
                continue

            # need to do the CBR on the notes_in_measure list:
            print('Retrieve:')
            candidate_set = cbr.retrieval(
                unadorned_measure,
                notes_in_measure[measure_number],
                database,
                complexity_weight=complexity_weight,
                difficulty_weight=difficulty_weight,
                method=retrieval_parameters.get('method', 'all'),
                similarity_threshold=retrieval_parameters.get(
                    'similarity_threshold', 100),
                percentile_range=retrieval_parameters.get(
                    'percentile_range', [0, 100]),
                adorned=retrieval_parameters.get('adorned', True),
                artists=retrieval_parameters.get('artists', 'all'),
                files=retrieval_parameters.get('files', 'all'),
                exclude_artists=retrieval_parameters.get(
                    'exclude_artists', ['none']),
                exclude_files=retrieval_parameters.get('exclude_files',
                                                       ['none']))
            # if nothing can be retrieved:
            if candidate_set == None:
                # append the measure to keep continuity and continue:
                new_measures.append(unadorned_measure)
                continue

            # get only the adorned_measure data:
            adorned_measures = [am.measure for am in candidate_set]
            del candidate_set

            print("Reuse:")
            new_measure = cbr.reuse(unadorned_measure, notes_in_measure[measure_number], adorned_measures,
                                    complexity_weight, difficulty_weight,
                                    weight_set, gp5_wellformedness)

            del adorned_measures

            revised_newly_adorned_measure = cbr.revise(
                new_measure.measure, revise_for_gp5=gp5_wellformedness)
            new_measures.append(revised_newly_adorned_measure)

            del new_measure

        new_song = parser.API.datatypes.Song(song.meta_data, new_measures)
        print("Revise:")
        new_song = cbr.revise(new_song, revise_for_gp5=gp5_wellformedness)
        new_songs.append(new_song)
        del new_song

    print("Retain:")
    new_song_file = cbr.retain(
        new_songs,
        gp5song=gp5song,
        song_title=song_title,
        database=database,
        artist_and_title_from_file_name=artist_and_title_from_file_name,
        add_to_database=add_to_database)
    return new_song_file


def run_action_reflection(gp5_file,
                          database,
                          complexity_weight=1,
                          difficulty_weight=1,
                          artist_and_title_from_file_name=False,
                          gp5_wellformedness=True,
                          add_to_database=True,
                          virtuosity_percentile=99,
                          virtuosity_similarity_threshold=0,
                          reflection_loop_limit=None,
                          similarity_threshold_relax_increment=10,
                          percentile_range_relax_increment=10,
                          similarity_threshold_limit=0,
                          percentile_limit=0,
                          **retrieval_parameters):
    """

    Parameters
    ---------
    gp5_file,
    database,
    complexity_weight=1,
    difficulty_weight=1,
    artist_and_title_from_file_name=False,
    gp5_wellformedness=True,
    add_to_database=True,
    virtuosity_percentile=99,
    virtuosity_similarity_threshold=0,
    no_improvement_limit=3,
    reflection_loop_limit=10,
    similarity_threshold_relax_increment=10,
    percentile_range_relax_increment=10,
    similarity_threshold_limit=0,
    percentile_limit=0



    """
    if isinstance(database, str):
        database = cbr.Database(database)
    else:
        assert isinstance(database,
                          cbr.Database), "database must be a database"

    # Read in the file:
    song_title = gp5_file.split(".")[0]
    gp5song = guitarpro.parse(gp5_file)

    if gp5song.title != "":
        song_title = gp5song.title

    api_songs = parser.API.get_functions.get_song_data(gp5song)
    song = api_songs[0]

    new_songs = []
    for track in range(0, len(api_songs)):
        song = api_songs[track]
        # for song in api_songs:
        # Combine tied notes and sort the list back into bars:
        note_list = parser.API.calculate_functions.calculate_tied_note_durations(
            api_songs[track])
        notes_in_measure = parser.API.calculate_functions.calculate_bars_from_note_list(
            note_list, api_songs[track])

        new_measures = []
        for unadorned_measure in song.measures:
            measure_number = unadorned_measure.meta_data.number - 1

            if not database.valid_measure(unadorned_measure,
                                          notes_in_measure[measure_number]):
                # append the measure to keep continuity and continue:
                new_measures.append(unadorned_measure)
                continue

            virtuosity_thresh = database.virtuosity_threshold(
                complexity_weight=complexity_weight,
                difficulty_weight=difficulty_weight,
                measure=unadorned_measure,
                notes_in_measure=notes_in_measure[measure_number],
                virtuosity_percentile=virtuosity_percentile,
                similarity_threshold=virtuosity_similarity_threshold)

            if virtuosity_thresh is None:
                # Fantastic doesn't work on the measure
                # so skip it
                print("can't get virtuosity_thresh")
                new_measures.append(unadorned_measure)
                continue

            revised_newly_adorned_measure, loop, loop_wni = action_reflection_loop(
                database,
                unadorned_measure,
                virtuosity_thresh,
                notes_in_measure=notes_in_measure[measure_number],
                complexity_weight=complexity_weight,
                difficulty_weight=difficulty_weight,
                gp5_wellformedness=gp5_wellformedness,
                reflection_loop_limit=reflection_loop_limit,
                similarity_threshold_relax_increment=
                similarity_threshold_relax_increment,
                percentile_range_relax_increment=
                percentile_range_relax_increment,
                similarity_threshold_limit=similarity_threshold_limit,
                percentile_limit=percentile_limit,
                method=retrieval_parameters.get('method', 'all'),
                similarity_threshold=retrieval_parameters.get(
                    'similarity_threshold', 100),
                percentile_range=retrieval_parameters.get(
                    'percentile_range', [0, 100]),
                adorned=retrieval_parameters.get('adorned', True),
                artists=retrieval_parameters.get('artists', 'all'),
                files=retrieval_parameters.get('files', 'all'),
                exclude_artists=retrieval_parameters.get(
                    'exclude_artists', ['none']),
                exclude_files=retrieval_parameters.get('exclude_files',
                                                       ['none']))

            new_measures.append(revised_newly_adorned_measure)

        print("Revise:")
        new_song = parser.API.datatypes.Song(song.meta_data, new_measures)
        new_song = cbr.revise(new_song, revise_for_gp5=gp5_wellformedness)
        new_songs.append(new_song)

    print("Retain:")
    new_song_file = cbr.retain(
        new_songs,
        gp5song=gp5song,
        song_title=song_title,
        database=database,
        artist_and_title_from_file_name=artist_and_title_from_file_name,
        add_to_database=add_to_database)

    return new_song_file


def action_reflection_loop(database,
                           unadorned_measure,
                           virtuosity_thresh,
                           notes_in_measure=[],
                           complexity_weight=1,
                           difficulty_weight=1,
                           weight_set='RD',
                           gp5_wellformedness=True,
                           reflection_loop_limit=None,
                           similarity_threshold_relax_increment=10,
                           percentile_range_relax_increment=10,
                           similarity_threshold_limit=0,
                           percentile_limit=0,
                           **retrieval_parameters):

    similarity_threshold = retrieval_parameters.get('similarity_threshold',
                                                    100)
    percentile_range = retrieval_parameters.get('percentile_range', [0, 100])

    revised_newly_adorned_measure = None

    reflection_loop_count = 0
    loops_without_improvement = 0

    if notes_in_measure == []:
        notes_in_measure = parser.API.calculate_functions.calculate_tied_note_durations(
            unadorned_measure)

    # While the virtuosity_test hasn't been passed
    # and the similarity_threshold and percentile_range
    # range parameters are within the range limits:
    while (similarity_threshold >= similarity_threshold_limit
           and similarity_threshold <= 100 and percentile_range[0] >= 0
           and percentile_range[1] <= 100
           and percentile_range[0] >= percentile_limit):
        print("reflection loop:", reflection_loop_count)
        print("reflection loop limit", reflection_loop_limit)
        print("similarity_threshold:", similarity_threshold)
        print("similarity_threshold_limit:", similarity_threshold_limit)
        print("percentile_range:", percentile_range)
        print("percentile_limit:", percentile_limit)
        print('Retrieve:')
        candidate_set = cbr.retrieval(
            unadorned_measure,
            notes_in_measure,
            database,
            complexity_weight=complexity_weight,
            difficulty_weight=difficulty_weight,
            method=retrieval_parameters.get('method', 'all'),
            similarity_threshold=similarity_threshold,
            percentile_range=percentile_range,
            adorned=retrieval_parameters.get('adorned', True),
            artists=retrieval_parameters.get('artists', 'all'),
            files=retrieval_parameters.get('files', 'all'),
            exclude_artists=retrieval_parameters.get('exclude_artists',
                                                     ['none']),
            exclude_files=retrieval_parameters.get('exclude_files', ['none']))
        # if nothing can be retrieved:
        if candidate_set == None:
            break

        # get only the adorned_measure data:
        adorned_measures = [am.measure for am in candidate_set]

        del candidate_set

        print("Reuse:")

        new_measure = cbr.reuse(unadorned_measure, notes_in_measure,
                                adorned_measures, complexity_weight,
                                difficulty_weight, weight_set,
                                gp5_wellformedness)
        del adorned_measures

        revised_newly_adorned_measure = cbr.revise(
            new_measure.measure, revise_for_gp5=gp5_wellformedness)
        del new_measure

        rnameasure_complexity = parser.API.calculate_functions.calculate_playing_complexity(
            revised_newly_adorned_measure,
            song=None,
            by_bar=False,
            calculation_type='both',
            weight_set=weight_set)

        # relax the similarity_threshold and percentile_range:
        similarity_threshold -= similarity_threshold_relax_increment

        min_range, max_range = percentile_range
        percentile_range = [
            min_range - percentile_range_relax_increment, max_range
        ]

        virtuosity_test = parser.API.calculate_functions.calculate_heuristic(
            rnameasure_complexity.BGM, virtuosity_thresh.complexity,
            rnameasure_complexity.EVC, virtuosity_thresh.difficulty,
            complexity_weight, difficulty_weight)

        if virtuosity_test >= 0:
            break

        # check to see if the loops need to be limited:
        reflection_loop_count += 1
        if reflection_loop_limit is not None:
            print("checking if loop should stop...")
            print("limit:", reflection_loop_limit, "count:",
                  reflection_loop_count)
            if reflection_loop_count >= reflection_loop_limit:
                break

    return revised_newly_adorned_measure, reflection_loop_count, loops_without_improvement


def make_database_from_gp5_folder(gp5files_folder,
                                  save_folder,
                                  files_to_add,
                                  move_tabs=True,
                                  save_feature_files=False,
                                  artist_and_title_from_file_name=True):
    """

    """

    files_to_add = glob.glob(gp5files_folder + "*.gp[3-5]")
    make_database(save_folder, files_to_add, move_tabs, save_feature_files,
                  artist_and_title_from_file_name)


def make_database(save_folder,
                  files_to_add,
                  move_tabs=True,
                  save_feature_files=False,
                  artist_and_title_from_file_name=True):
    """

    """

    database = cbr.Database(save_folder)
    database.add_entries_from_list_of_gp5_files(
        files_to_add, move_tabs, save_feature_files,
        artist_and_title_from_file_name)

    return


def run_virtuosity_thesh_action_reflection(
        gp5_file,
        database,
        song_title=None,
        complexity_weight=1,
        difficulty_weight=1,
        weight_set='RD',
        artist_and_title_from_file_name=False,
        gp5_wellformedness=True,
        add_to_database=True,
        similarity_threshold=99,
        similarity_threshold_relax_increment=1,
        similarity_threshold_limit=0,
        virtuosity_percentile=99,
        percentile_search_expand_range=1,
        comprehensive_search=False,
        fixed_virtuosity_threshold=None,
        loops_without_improvement_limit=None,
        **retrieval_parameters):
    """

    Parameters
    ---------
    gp5_file,
    database,
    complexity_weight=1,
    difficulty_weight=1,
    retrieval_method='all',
    similarity_threshold=100,
    artist_and_title_from_file_name=False,
    gp5_wellformedness=True



    """
    if isinstance(database, str):
        database = cbr.Database(database)
    else:
        assert isinstance(database,
                          cbr.Database), "database must be a database"

    # Read in the file:
    if song_title is None:
        song_title = gp5_file.split(".")[0]
    gp5song = guitarpro.parse(gp5_file)

    if gp5song.title != "":
        song_title = gp5song.title

    api_songs = parser.API.get_functions.get_song_data(gp5song)
    song = api_songs[0]

    # sort out the fixed threshold:
    if fixed_virtuosity_threshold is not None:
        if not isinstance(fixed_virtuosity_threshold,
                          cbr.database.VirtuosityThreshold):
            if isinstance(fixed_virtuosity_threshold, list) or isinstance(
                    fixed_virtuosity_threshold, tuple):
                if len(fixed_virtuosity_threshold) == 2:
                    fixed_virtuosity_threshold = cbr.database.VirtuosityThreshold(
                        fixed_virtuosity_threshold[0],
                        fixed_virtuosity_threshold[1], [])

    new_songs = []
    for track in range(0, len(api_songs)):
        song = api_songs[track]
        # for song in api_songs:
        # Combine tied notes and sort the list back into bars:
        note_list = parser.API.calculate_functions.calculate_tied_note_durations(
            api_songs[track])
        notes_in_measure = parser.API.calculate_functions.calculate_bars_from_note_list(
            note_list, api_songs[track])

        new_measures = []
        for unadorned_measure in song.measures:

            print("Working on....")
            print("Song:", song_title)
            print("Track:", track)
            print("Measure:", unadorned_measure.meta_data.number)

            checked_pieces = []

            # measure_number is an index.
            measure_number = unadorned_measure.meta_data.number - 1

            if not database.valid_measure(unadorned_measure,
                                          notes_in_measure[measure_number]):
                # append the measure to keep continuity and continue:
                new_measures.append(unadorned_measure)
                continue

            unadorned_measure_complexity = parser.API.calculate_functions.calculate_playing_complexity(
                unadorned_measure,
                song=None,
                by_bar=False,
                calculation_type='both',
                weight_set=weight_set,
                unadorned_value=True)

            print(unadorned_measure_complexity)

            measure_virtuosity_threshold = database.virtuosity_threshold(
                complexity_weight,
                difficulty_weight,
                measure=unadorned_measure,
                notes_in_measure=notes_in_measure[measure_number],
                virtuosity_type='performance',
                virtuosity_percentile=virtuosity_percentile,
                similarity_threshold=similarity_threshold,
                percentile_range=retrieval_parameters.get(
                    'percentile_range', [0, 100]),
                adorned=retrieval_parameters.get('adorned', True),
                artists=retrieval_parameters.get('artists', 'all'),
                files=retrieval_parameters.get('files', 'all'),
                exclude_artists=retrieval_parameters.get(
                    'exclude_artists', ['none']),
                exclude_files=retrieval_parameters.get('exclude_files',
                                                       ['none']))
            """
            # compare the calculated virtuosity threshold with the
            # unadorned measure and pick the best
            # complexity and difficulty between them:
            best_virtuosity_threshold = parser.API.calculate_functions.calculate_heuristic(
                unadorned_measure_complexity.BGM,
                measure_virtuosity_threshold.complexity,
                unadorned_measure_complexity.EVC,
                measure_virtuosity_threshold.difficulty, complexity_weight,
                difficulty_weight)
            if best_virtuosity_threshold > 0:
                measure_virtuosity_threshold = measure_virtuosity_threshold._replace(
                    complexity=unadorned_measure_complexity.BGM,
                    difficulty=unadorned_measure_complexity.EVC)
                #measure_virtuosity_threshold.complexity = unadorned_measure_complexity.BGM
                #measure_virtuosity_threshold.difficulty = unadorned_measure_complexity.EVC
            """

            # then check if the virtuosity threshold is pre-fixed:
            if fixed_virtuosity_threshold is None:
                virtuosity_threshold = measure_virtuosity_threshold
            else:
                virtuosity_threshold = fixed_virtuosity_threshold

            print(virtuosity_threshold.complexity,
                  virtuosity_threshold.difficulty)

            pieces = measure_virtuosity_threshold.pieces
            checked_pieces += pieces

            # get only the adorned_measure data:
            # adorned_measures = map(lambda am: am.measure, candidate_set)
            best_measure = None
            virtuosity_test = 0
            reflection_loop_count = 0
            loops_since_last_improvement = 0

            for s_thresh in range(
                    similarity_threshold, similarity_threshold -
                    similarity_threshold_relax_increment,
                    -similarity_threshold_relax_increment):

                clear_console()
                print("Working on....")
                print("Song:", song_title)
                print("Track:", track)
                print("Measure:", unadorned_measure.meta_data.number)
                print("Starting reflection loop:", reflection_loop_count)
                print("similarity_threshold:", s_thresh)
                print("Possible New Candidates:", len(pieces))

                no_improvement = False
                virtuosity_thres_passed = False
                # percentile_searched_up_to = None
                upper_percentile_searched_up_to = None
                lower_percentile_searched_up_to = None

                #percentile_expansion_factor = 1
                number_of_upper_expansions = (
                    100 -
                    virtuosity_percentile) / percentile_search_expand_range
                number_of_lower_expansions = virtuosity_percentile / percentile_search_expand_range

                for percentile_range in range(
                        1,
                        int(
                            round(
                                max([
                                    number_of_upper_expansions,
                                    number_of_lower_expansions
                                ]))) + 1):

                    #for v_percetile in range(
                    #        virtuosity_percentile,
                    #        virtuosity_percentile_limit - percentile_range,
                    #        -percentile_range):

                    if upper_percentile_searched_up_to is not None or lower_percentile_searched_up_to is not None:
                        if (virtuosity_percentile + int(
                                round(percentile_range / 2)) <
                                upper_percentile_searched_up_to
                                or virtuosity_percentile - int(
                                    round(percentile_range / 2)) >
                                lower_percentile_searched_up_to):
                            continue

                    v_upper = virtuosity_percentile + int(
                        round(percentile_range / 2))
                    if v_upper >= 100:
                        v_upper = 100

                    v_lower = virtuosity_percentile - int(
                        round(percentile_range / 2))
                    if v_lower <= 0:
                        v_lower = 0

                    print("virtuosity upper percentile:", v_upper)
                    print("virtuosity lower percentile:", v_lower)
                    candidate_pieces, upper_percentile_searched_up_to, lower_percentile_searched_up_to = pick_percentile_pieces(
                        pieces, virtuosity_percentile, percentile_range)

                    candidate_set = prep_and_get_pieces_data(
                        candidate_pieces, database)

                    print("Candidates:", len(candidate_set))

                    #print("Reuse:")
                    new_measure = cbr.reuse(
                        unadorned_measure=unadorned_measure,
                        unadorned_measure_notes=notes_in_measure[
                            measure_number],
                        adorned_measures=candidate_set,
                        complexity_weight=complexity_weight,
                        difficulty_weight=difficulty_weight,
                        weight_set=weight_set,
                        gp5_wellformedness=gp5_wellformedness)

                    revised_newly_adorned_measure = new_measure.measure
                    assert len(revised_newly_adorned_measure.notes) == len(
                        notes_in_measure[measure_number])

                    revised_newly_adorned_measure_complexity = new_measure.complexity
                    # revised_newly_adorned_measure = cbr.revise(
                    #    new_measure.measure, revise_for_gp5=gp5_wellformedness)

                    # revised_newly_adorned_measure_complexity = parser.API.calculate_functions.calculate_playing_complexity(
                    #    revised_newly_adorned_measure,
                    #    song=None,
                    #    by_bar=False,
                    #    calculation_type='both',
                    #    weight_set='RD')

                    if best_measure is None:
                        best_measure = BestMeasure(
                            revised_newly_adorned_measure,
                            revised_newly_adorned_measure_complexity.BGM,
                            revised_newly_adorned_measure_complexity.EVC)
                    else:
                        best_measure_test = parser.API.calculate_functions.calculate_heuristic(
                            revised_newly_adorned_measure_complexity.BGM,
                            best_measure.complexity,
                            revised_newly_adorned_measure_complexity.EVC,
                            best_measure.difficulty, complexity_weight,
                            difficulty_weight)
                        if best_measure_test > 0:
                            best_measure = BestMeasure(
                                revised_newly_adorned_measure,
                                revised_newly_adorned_measure_complexity.BGM,
                                revised_newly_adorned_measure_complexity.EVC)
                            no_improvement = False
                        else:
                            no_improvement = True

                    virtuosity_test = parser.API.calculate_functions.calculate_heuristic(
                        best_measure.complexity,
                        virtuosity_threshold.complexity,
                        best_measure.difficulty,
                        virtuosity_threshold.difficulty, complexity_weight,
                        difficulty_weight)

                    if virtuosity_test > 0:
                        virtuosity_thres_passed = True
                        break

                    # clear variables:
                    del candidate_set, candidate_pieces

                    if not comprehensive_search:
                        break

                # see if the loops_since_last_improvement has
                # surpassed the loops_without_improvement_limit
                if no_improvement:
                    loops_since_last_improvement += 1
                if loops_without_improvement_limit is not None:
                    if loops_since_last_improvement > loops_without_improvement_limit:
                        break
                """
                virtuosity_test = parser.API.calculate_functions.calculate_heuristic(
                    best_measure.complexity, virtuosity_threshold.complexity,
                    best_measure.difficulty, virtuosity_threshold.difficulty,
                    complexity_weight, difficulty_weight)
                """

                if virtuosity_thres_passed:
                    break

                # relax the similarity threshold:
                #similarity_threshold -= similarity_threshold_relax_increment

                #if similarity_threshold < 0 or similarity_threshold < similarity_threshold_limit:
                #    break

                # get the new candidate set:
                new_virtuosity = database.virtuosity_threshold(
                    complexity_weight,
                    difficulty_weight,
                    measure=unadorned_measure,
                    notes_in_measure=notes_in_measure[measure_number],
                    virtuosity_type='performance',
                    virtuosity_percentile=virtuosity_percentile,
                    similarity_threshold=s_thresh,
                    percentile_range=retrieval_parameters.get(
                        'percentile_range', [0, 100]),
                    adorned=retrieval_parameters.get('adorned', True),
                    artists=retrieval_parameters.get('artists', 'all'),
                    files=retrieval_parameters.get('files', 'all'),
                    exclude_artists=retrieval_parameters.get(
                        'exclude_artists', ['none']),
                    exclude_files=retrieval_parameters.get(
                        'exclude_files', ['none']))
                del pieces
                pieces = new_virtuosity.pieces
                pieces = check_pieces(pieces, checked_pieces)
                checked_pieces += pieces
                del new_virtuosity

                reflection_loop_count += 1

                # if nothing can be retrieved:
                # if consolidated_ids_to_files == None or consolidated_ids_to_files == {}:
                # append the measure to keep continuity and continue:
                #    new_measures.append(unadorned_measure)
                #    continue

            assert len(revised_newly_adorned_measure.notes) == len(
                notes_in_measure[measure_number])

            new_measures.append(best_measure.measure)
            del best_measure, checked_pieces

        new_song = parser.API.datatypes.Song(song.meta_data, new_measures)

        for unadorned_measure, new_measure in zip(song.measures,
                                                  new_song.measures):
            assert len(
                parser.API.calculate_functions.calculate_tied_note_durations(
                    unadorned_measure)) == len(new_measure.notes)

        print("Revise:")
        new_song = cbr.revise(new_song, revise_for_gp5=gp5_wellformedness)

        for unadorned_measure, new_measure in zip(song.measures,
                                                  new_song.measures):

            measure_number = unadorned_measure.meta_data.number - 1
            assert len(notes_in_measure[measure_number]) == len(
                new_measure.notes)

        new_songs.append(new_song)

        del new_measures

    print("Retain:")
    new_song_file = cbr.retain(
        api_song_data=new_songs,
        song_title=song_title,
        database=database,
        artist_and_title_from_file_name=artist_and_title_from_file_name,
        add_to_database=add_to_database)

    return new_song_file, new_songs


def pick_percentile_pieces(pieces, virtuosity_percentile, percentile_range=1):

    percent = len(pieces) / 100

    # if the
    percentile_index = int(ceil((100 - virtuosity_percentile) * percent))

    # check the index doesn't exceed the number of pieces
    if percentile_index >= len(pieces):
        percentile_index = len(pieces) - 1
    if percentile_index < 0:
        percentile_index = 0

    range_increment = int(round(percentile_range / 2))

    upper_percentile_range_index = int(
        floor(percentile_index - percent * range_increment))
    lower_percentile_range_index = int(
        ceil(percentile_index + percent * range_increment))

    # if upper_percentile >= the max then limit it
    # and subtract the range that would have been added
    # to the upper percentile from the lower one:
    if upper_percentile_range_index <= 0:
        upper_percentile_range_index = 0
        lower_percentile_range_index += range_increment

    if lower_percentile_range_index >= len(pieces):
        lower_percentile_range_index = len(pieces) - 1
        if (upper_percentile_range_index - range_increment) > 0:
            upper_percentile_range_index -= range_increment
        else:
            upper_percentile_range_index = 0

    print('percentile_index:', percentile_index)
    print('upper_percentile_range_index:', upper_percentile_range_index)
    print('lower_percentile_range_index:', lower_percentile_range_index)
    print('range:',
          (lower_percentile_range_index - upper_percentile_range_index))
    print('total possible candidates:', len(pieces))
    print(
        'selected candidates:',
        len(pieces[upper_percentile_range_index:lower_percentile_range_index +
                   1]))

    if lower_percentile_range_index == upper_percentile_range_index:
        if lower_percentile_range_index >= len(pieces):
            lower_percentile_range_index = len(pieces) - 1

        selected_pieces = [pieces[lower_percentile_range_index]]

    else:
        selected_pieces = pieces[upper_percentile_range_index:
                                 lower_percentile_range_index + 1]

    #lower_percentile_searched_up_to = 100 - percentile_index / percent

    # need to convert the index back to a percentage, i'm not doing this here:

    lower_percentile_searched_up_to = (
        (lower_percentile_range_index // len(pieces)) * 100)

    upper_percentile_searched_up_to = (
        (upper_percentile_range_index // len(pieces)) * 100)

    #print(upper_percentile_searched_up_to, lower_percentile_searched_up_to)

    return selected_pieces, upper_percentile_searched_up_to, lower_percentile_searched_up_to


def prep_and_get_pieces_data(pieces, database):
    # get only the ids...
    initial_candidates = [p.id for p in pieces]

    candidate_set_ids = []
    for c_id in initial_candidates:
        for i in c_id:
            candidate_set_ids.append(i)

    #consolidated_ids_to_files = database.consolidate_multiple_entries_from_same_files(
    #    candidate_set_ids)

    # load the data:
    return database.retrieve_data_from_multiple_entries(candidate_set_ids)


def check_pieces(pieces, check_pieces):
    """Remove pieces that have been checked previously
    from being checked again.

    """
    for p in pieces:
        if p in check_pieces:
            pieces.remove(p)

    return pieces


def virtuosity_theshold_mapping(value, linear=False):
    """ maps a value between 0 and 1 to a similarity threshold and
    percentile.

    """
    assert value <= 1 and value >= 0, "value must be between 0 and 1"
    mapping = namedtuple('VirtuosityMapping',
                         ['similarity_threshold', 'virtuosity_percentile'])
    if linear:
        percentile = floor(value * 99)
        sim_thresh = 100 - value * 100
        return
    else:
        sim_thresh = round(log10(10 - value * 9) * 99)
        percentile = floor(log10(value * 9 + 1) * 99)

    return mapping(int(sim_thresh), int(percentile))
