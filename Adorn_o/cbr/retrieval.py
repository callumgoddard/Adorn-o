from collections import namedtuple
import warnings

from ..parser.API.datatypes import Measure, AdornedNote
from ..parser.API.calculate_functions import calculate_heuristic

# Named tuples for external access:
retieved = namedtuple("Retrieved", ["id", "measure"])
candidate = namedtuple("Candidates", ["complexity", "difficulty", "id"])


def retrieval(
    measure,
    measure_notes,
    database,
    complexity_weight,
    difficulty_weight,
    **retrieval_parameters
):
    """Retrieve the database entry that closest matches the measure input.

    Parameters
    ---------
    measure_notes :

    measure : Measure, list of Measures
        A measure in Measure format, or a list of measures in measure format

    database : an instance of cbr.Database()

    method : {'all', 'best', int}
        indication of what measures to retrieve.
            'all' : all the measures that meet
            the similarity_threshold will be returned
            'best' : the measure with the best complexity and difficulty
            according to the complexity_weight and difficulty_weight
            is returned
            int : the x number of measures with the best complexity
            and difficulty according to the complexity_weight and
            difficulty_weight are returned

    complexity_weight, difficulty_weight : {-1.0 - 1.0}

    find_most_similar_params : dict, (optional)
        similarity_threshold : {0 - 100}
        percentile_range : [min_percentile, max_percentile]
        adorned : boolean
        artists : list, 'all'
        files : list, 'all'
        exclude_artists : list, ['none']
        exclude_files : list, ['none']

    Returns
    ------

    list of namedtuples
        a list of Retrieved tuples

    """

    for note in measure_notes:
        assert isinstance(note, AdornedNote), ("%s is not type %s" % note, AdornedNote)
    assert isinstance(measure, Measure), "measure is not type %s" % Measure

    # sort out the find_most_similar_params:
    # invert the similarity percent:
    method = retrieval_parameters.get("method", "all")

    print("measure notes:", measure_notes)
    print(retrieval_parameters)

    # Perform some selection on the candidate set:
    candidate_set = database.find_most_similar(
        measure,
        notes_in_measure=measure_notes,
        complexity_weight=complexity_weight,
        difficulty_weight=difficulty_weight,
        similarity_threshold=retrieval_parameters.get("similarity_threshold", 100),
        percentile_range=retrieval_parameters.get("percentile_range", [0, 100]),
        adorned=retrieval_parameters.get("adorned", True),
        artists=retrieval_parameters.get("artists", "all"),
        files=retrieval_parameters.get("files", "all"),
        exclude_artists=retrieval_parameters.get("exclude_artists", ["none"]),
        exclude_files=retrieval_parameters.get("exclude_files", ["none"]),
    )

    sorted_candidates = database.sort_candidate_set(
        candidate_set, complexity_weight, difficulty_weight
    )

    # check there are candidates:
    if sorted_candidates == []:
        return None

    if method == "best":
        if complexity_weight == 0 and difficulty_weight == 0:
            warnings.warn(
                "complexity_weight and difficulty_weight are 0."
                + "selected_candidates may not be what is expected"
            )
        print("best")
        selected_candidates = pick_top_candidate_ids(sorted_candidates, 1)
    if isinstance(method, int):
        if complexity_weight == 0 and difficulty_weight == 0:
            warnings.warn(
                "complexity_weight and difficulty_weight are 0."
                + "selected_candidates may not be what is expected"
            )

        print("Picking top %s..." % method)
        selected_candidates = pick_top_candidate_ids(sorted_candidates, method)
        print(selected_candidates)
    if method == "all":
        print("all")
        print(sorted_candidates)
        selected_candidates = pick_top_candidate_ids(
            sorted_candidates, len(sorted_candidates)
        )

    return retrieve_candidate_data(selected_candidates, database)


def retrieve_candidate_data(selected_candidates, database):

    unsorted_retrieved_measures = database.retrieve_data_from_multiple_entries(
        selected_candidates, True
    )

    unsorted_retrieved_measures_id_list = [m.id for m in unsorted_retrieved_measures]

    # then match the order of the candidates:

    retrieved_measures = []
    for selected_candidate in selected_candidates:
        index = unsorted_retrieved_measures_id_list.index(selected_candidate)
        retrieved_measures.append(unsorted_retrieved_measures[index])

    #    retrieved_measures.append(
    #        retieved(selected_candidate,
    #                 database.retrieve_entry_data(selected_candidate)))

    return retrieved_measures


"""
def sort_candidate_set(candidate_set, database, complexity_weight,
                       difficulty_weight):
    sorted_candidates = []

    # load the database:
    database.load()

    complexity_index = database.header.index('complexity')
    difficulty_index = database.header.index("perceived.difficulty")

    # sort the candidate ids by the heuristic:
    for candidate_id in candidate_set:
        candidate_entry = database.data.get(candidate_id)

        index = 0
        for sorted_candidate in sorted_candidates:
            heuristic = calculate_heuristic(
                float(candidate_entry[complexity_index]),
                float(sorted_candidate.complexity),
                float(candidate_entry[difficulty_index]),
                float(sorted_candidate.difficulty), complexity_weight,
                difficulty_weight)
            if heuristic >= 0:
                break
            index += 1
        sorted_candidates.insert(
            index,
            candidate(
                complexity=float(candidate_entry[complexity_index]),
                difficulty=float(candidate_entry[difficulty_index]),
                id=candidate_id))

    return sorted_candidates
"""


def pick_top_candidate_ids(sorted_candidates, top_n):

    consolidated_candidates = consolidate_same_complexity_difficulty(sorted_candidates)

    return select_top_n_consolidated(consolidated_candidates, top_n)


def consolidate_same_complexity_difficulty(sorted_candidates):

    top_candidates = [
        candidate(
            sorted_candidates[0].complexity,
            sorted_candidates[0].difficulty,
            [sorted_candidates[0].id],
        )
    ]

    top_count = 0
    for s_c in sorted_candidates[1:]:

        if (
            s_c.complexity == top_candidates[top_count].complexity
            and s_c.difficulty == top_candidates[top_count].difficulty
        ):
            top_candidates[top_count].id.append(s_c.id)
        else:
            top_candidates.append(candidate(s_c.complexity, s_c.difficulty, [s_c.id]))
            top_count += 1
    return top_candidates


def select_top_n_consolidated(consolidated_candidates, top_n):

    top_ids = []
    top_count = 1
    for t_c in consolidated_candidates:
        for c_id in t_c.id:
            top_ids.append(c_id)
        if top_count >= top_n:
            break
        top_count += 1
    return top_ids
