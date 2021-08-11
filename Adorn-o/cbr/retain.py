from __future__ import division, print_function, absolute_import

import uuid
import os
import json

import guitarpro

import cbr
from parser.API.get_functions import get_song_data
import parser.API.write_functions
import parser.API.datatypes

# Take the revised song/measure/whatever

# load in the original gp5 file and transfer the adornements from the
# revised measure into the freshly loaded api data,
# based on the note numbers

# then convert back to gp5 and write the file out. Then load the freshly
# made gp5 file back into the database to retain it.


def retain(api_song_data, song_title, database, **kwargs):
    """Performs the retain stage of the CBR

    """

    if isinstance(api_song_data, list):
        for song in api_song_data:
            assert isinstance(song, parser.API.datatypes.Song)
    else:
        assert isinstance(api_song_data, parser.API.datatypes.Song)

    assert isinstance(database, cbr.Database)

    output_location = kwargs.get('output_location',
                                 database.save_folder + "/output/")

    artist_and_title_from_file_name = kwargs.get(
        'artist_and_title_from_file_name', True)
    move_tabs = kwargs.get('move_tabs', False)
    add_to_database = kwargs.get('add_to_database', True)

    assert isinstance(artist_and_title_from_file_name, bool)

    file_out = output_file_name(output_location, song_title)

    check_output_path(output_location)

    # Write out the file:
    if isinstance(api_song_data, list):
        json_data, json_dict = parser.API.write_functions.api_to_json(
            api_song_data)
    elif isinstance(api_song_data, parser.API.datatypes.Song):

        json_data, json_dict = parser.API.write_functions.api_to_json(
            [api_song_data])

    with open(file_out, 'w') as write_file:
        json.dump(
            json_dict,
            write_file,
            indent=4,
        )

    # add the song to the database
    if add_to_database:
        database.add_entries_from_json_file(
            json_file=file_out,
            move_tabs=move_tabs,
            remove_duplicates=True,
            save_feature_files=False,
            artist_and_title_from_file_name=artist_and_title_from_file_name)

    return file_out


def check_output_path(gp5_file_out):
    try:
        if not os.path.isdir(gp5_file_out):
            os.makedirs(gp5_file_out)
            return True
    except OSError:
        print("Creation of the directory %s failed" % gp5_file_out)
        return False


def output_file_name(gp5_file_out, song_title):
    song_title = song_title.replace(' ', '_')
    file_out = str(gp5_file_out + song_title + ".json")
    if os.path.isfile(str(gp5_file_out + song_title + ".json")):

        file_out = str(gp5_file_out + song_title + str(uuid.uuid4())[:8] +
                       ".json")
    return file_out
