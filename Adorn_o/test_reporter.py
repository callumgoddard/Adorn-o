

from cbr import Database

import guitarpro

from parser.API import get_functions

database = Database('database')

input_file = './database/input/The Supremes - Love Is Like An Itching In My Heart.gp5'
output_file = './database/output/Love_Is_Like_An_Itching_In_My_Heartd3fc1102.gp5'

gp_data = guitarpro.parse(input_file)

api_data = get_functions.get_song_data(gp_data)
api_song = api_data[0]

threshold = database.virtuosity_threshold(
    complexity_weight=1,
    difficulty_weight=1,
    measure=api_song.measures[0],
    notes_in_measure=[],
    virtuosity_type='performance',
    virtuosity_percentile=99,
    similarity_threshold=90)

print(threshold.pieces)
print(len(threshold.pieces))

print([p.id for p in threshold.pieces])
"""
database.produce_report(
    input_file,
    output_file,
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
    percentile_range=[99, 100])
"""
