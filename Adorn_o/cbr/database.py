import os
import csv
import uuid
from collections import namedtuple
import re
import shutil
import json
from fractions import Fraction

# 3rd party imports
import rpy2.robjects as robjects
import guitarpro

# Application imports:
from ..parser.API.datatypes import Measure, AdornedNote, Song, Rest
from ..parser.API import get_functions, write_functions
from ..parser.API.calculate_functions import (
    calculate_tied_note_durations,
    calculate_bars_from_note_list,
    calculate_grace_note_possitions,
    calculate_midi_file_for_measure_note_list,
    calculate_rhy_file_for_measure,
    calculate_playing_complexity,
    calculate_heuristic,
)
from ..parser.utilities import run_melconv
from .. import feature_analysis
from ..evaluation import musiplectics

from .. import cbr

accepted_time_sigs = []

sorted = namedtuple("Sorted", ["adorned", "complexity_weight", "difficulty_weight"])

VirtuosityThreshold = namedtuple(
    "VirtuosityThreshold", ["complexity", "difficulty", "pieces"]
)
candidate = namedtuple("Candidates", ["complexity", "difficulty", "id"])
retieved = namedtuple("Retrieved", ["id", "measure"])
modified_notes = namedtuple(
    "ModifiedNotes", ["measure", "total_modified", "proportion"]
)

remove_bad_chars = re.compile("[^a-zA-Z]")


class Database:
    """ """

    def __init__(self, save_folder="./", new_database=False, weight_set="GMS"):
        """ """
        if "." != save_folder.split("/")[0]:
            save_folder = "./" + save_folder
        self.data_location = save_folder + "/" + "database.csv"
        self.save_folder = save_folder
        self.gpfiles_location = save_folder + "/gpfiles"
        self.json_location = save_folder + "/json"
        self.last_processed_file = None
        self.data = None
        self.weight_set = weight_set
        self.header = [
            "file.id",
            "file.location",
            "artist",
            "song.title",
            "track",
            "measure.number",
            "complexity",
            "perceived.difficulty",
            "unadorned.complexity",
            "unadorned.perceived.difficulty",
            "single.note",
            "single.note.pitch",
            "single.note.fret.number",
            "single.note.string.number",
            "single.note.duration",
            "mean.entropy",
            "mean.productivity",
            "mean.Simpsons.D",
            "mean.Yules.K",
            "mean.Sichels.S",
            "mean.Honores.H",
            "p.range",
            "p.entropy",
            "p.std",
            "i.abs.range",
            "i.abs.mean",
            "i.abs.std",
            "i.mode",
            "i.entropy",
            "d.range",
            "d.median",
            "d.mode",
            "d.entropy",
            "d.eq.trans",
            "d.half.trans",
            "d.dotted.trans",
            "len",
            "glob.duration",
            "note.dens",
            "tonalness",
            "tonal.clarity",
            "tonal.spike",
            "int.cont.grad.mean",
            "int.cont.grad.std",
            "int.cont.dir.change",
            "step.cont.glob.var",
            "step.cont.glob.dir",
            "step.cont.loc.var",
            "mode",
            "h.contour",
            "int.cont.glob.dir",
            "int.contour.class",
            "PRS.mean_syncopation_per_bar",
            "KTH.mean_syncopation_per_bar",
            "LHL.mean_syncopation_per_bar",
            "SG.mean_syncopation_per_bar",
            "TMC.mean_syncopation_per_bar",
            "TOB.mean_syncopation_per_bar",
            "WNBD.mean_syncopation_per_bar",
        ]

        # Load r related things:
        feature_analysis.fantastic_interface.load()

        if new_database is False:
            # if the file doesn't exist - make it
            if not os.path.isfile(self.data_location):
                self.make_new_database()
        else:
            self.make_new_database()

        if os.path.isfile(self.save_folder + "/last_processed_file.txt"):
            last_file = open(self.save_folder + "/last_processed_file.txt")
            self.last_processed_file = last_file.read()

        if os.path.isfile(self.save_folder + "/sorted.txt"):
            sorted_file = open(self.save_folder + "/sorted.txt")
            sorted_info = []
            for line in sorted_file:
                sorted_info.append(line.rstrip())

            if sorted_info == []:
                self.sorted = sorted(None, None, None)

            elif sorted_info[0] == "False":
                self.sorted = sorted(
                    False, float(sorted_info[1]), float(sorted_info[2])
                )
            elif sorted_info[0] == "True":
                self.sorted = sorted(True, float(sorted_info[1]), float(sorted_info[2]))
        else:
            self.sorted = sorted(None, None, None)

    def make_new_database(self):

        try:
            if not os.path.isdir(self.save_folder):
                # make the directory structure:
                os.makedirs(self.save_folder + "/gpfiles")
                os.makedirs(self.save_folder + "/json")
                os.makedirs(self.save_folder + "/raw_entry_tables")
                os.makedirs(self.save_folder + "/output/reports/")
            else:
                print("%s folder already exists" % self.save_folder)
                # check if there are folders missing and make them:
                if not os.path.isdir(self.save_folder + "/gpfiles"):
                    os.makedirs(self.save_folder + "/gpfiles")
                if not os.path.isdir(self.save_folder + "/json"):
                    os.makedirs(self.save_folder + "/json")
                if not os.path.isdir(self.save_folder + "/raw_entry_tables"):
                    os.makedirs(self.save_folder + "/raw_entry_tables")
                if not os.path.isdir(self.save_folder + "/output/reports/"):
                    os.makedirs(self.save_folder + "/output/reports/")

        except OSError:
            print("Creation of the directory %s failed" % self.data_location)
            return

        with open(self.data_location, mode="w") as data_base_file:
            data_base_updater = csv.writer(data_base_file)
            data_base_updater.writerow(self.header)
        with open(self.save_folder + "/sorted.txt", mode="w") as sorted_savefile:
            sorted_savefile.write("")

    def load_gp_file(self, gp5_file):
        try:
            print("Loading %s" % gp5_file)
            gp5song = guitarpro.parse(gp5_file)
            api_song_data = get_functions.get_song_data(gp5song)
            return api_song_data
        except:
            print("Unable to load %s" % gp5_file)
            return False

    def load_json_file(self, json_file):
        try:
            with open(json_file) as read_file:
                json_data = json.load(read_file)
            api_song_data = get_functions.get_from_JSON(json_data)
            return api_song_data
        except:
            print("Unable to load %s" % json_file)
            return False

    def load_file(self, file_location):
        song = False
        print(file_location)
        if "json" in file_location.split("."):
            print("json found")
            song = self.load_json_file(file_location)
        else:
            song = self.load_gp_file(file_location)

        return song

    def track_id(self, song_title, track):
        return str(song_title) + "_track_" + str(track)

    def measure_id(self, track_id, measure_number):
        return track_id + "_bar_" + str(measure_number)

    def add_entries_from_list_of_gp5_files(
        self,
        list_of_gp5_files,
        convert_to_json=True,
        move_tabs=True,
        remove_duplicates=True,
        save_feature_files=False,
        artist_and_title_from_file_name=True,
    ):
        assert isinstance(list_of_gp5_files, list), "list_of_gp5_files is not a list"
        for gp5_file in list_of_gp5_files:
            print("Adding measures in %s to database..." % gp5_file)
            self.add_entries_from_gp5_file(
                gp5_file,
                move_tabs=move_tabs,
                remove_duplicates=remove_duplicates,
                save_feature_files=save_feature_files,
                artist_and_title_from_file_name=artist_and_title_from_file_name,
            )

    def add_entries_from_gp5_file(
        self,
        gp5_file,
        convert_to_json=True,
        process_tied_notes_in_json=True,
        move_tabs=True,
        remove_duplicates=True,
        save_feature_files=False,
        artist_and_title_from_file_name=True,
    ):
        """
        Add entries to the database from the gp5_file
        '"""
        if move_tabs:
            # move the tab
            if not os.path.isfile(self.gpfiles_location + "/" + gp5_file):
                shutil.move(gp5_file, self.gpfiles_location)
                # update the tab location to be loaded.
                gp5_file = "gpfiles/" + gp5_file.split("/")[-1]
            else:
                print("File already in database gpfiles folder")

        # save a record of the last processed file:
        last_processed_file = open(
            self.save_folder + "/" + "last_processed_file.txt", "w"
        )
        last_processed_file.write(gp5_file)
        last_processed_file.close()

        if move_tabs:
            api_song_data = self.load_gp_file(self.save_folder + "/" + gp5_file)
        else:
            api_song_data = self.load_gp_file(gp5_file)

        if api_song_data is False:
            print("unable to add entry for %s" % gp5_file)
            return

        # Strip out the file extension, but keep any '.' in the sone name:
        song_file_name_no_path_no_ext = ""
        for part in gp5_file.split("/")[-1].split(".")[:-1]:
            song_file_name_no_path_no_ext += part
            if (
                gp5_file.split("/")[-1].split(".")[:-1].index(part)
                != len(gp5_file.split("/")[-1].split(".")[:-1]) - 1
            ):
                song_file_name_no_path_no_ext += "."

        json_file = None
        if convert_to_json:

            if process_tied_notes_in_json:
                api_processed_tied_notes = []

                for track in api_song_data:
                    note_list = calculate_tied_note_durations(track)
                    notes_in_measure = calculate_bars_from_note_list(note_list, track)

                    measures_with_processed_tied_notes = []
                    for measure in track.measures:
                        measures_with_processed_tied_notes.append(
                            Measure(
                                meta_data=measure.meta_data,
                                start_time=measure.start_time,
                                notes=notes_in_measure[measure.meta_data.number - 1],
                            )
                        )

                    api_processed_tied_notes.append(
                        Song(
                            meta_data=track.meta_data,
                            measures=measures_with_processed_tied_notes,
                        )
                    )

                api_song_data = api_processed_tied_notes

            json_data, json_dict = write_functions.api_to_json(api_song_data)
            json_file = "json/" + song_file_name_no_path_no_ext + ".json"

            if os.path.isfile(
                self.save_folder + "/json/" + song_file_name_no_path_no_ext + ".json"
            ):

                json_file = str(
                    "json/"
                    + song_file_name_no_path_no_ext
                    + " "
                    + str(uuid.uuid4())[:8]
                    + ".json"
                )

            with open(self.save_folder + "/" + json_file, "w") as write_file:
                json.dump(
                    json_dict,
                    write_file,
                    indent=4,
                )

            # Check the JSON file:
            json_api_song_data = self.load_file(self.save_folder + "/" + json_file)

            assert json_api_song_data == api_song_data
            """
            # test code to debug if assert json_api_song_data == api_song_data fails
            for j_song_data, a_song_data in zip(json_api_song_data, api_song_data):
                assert j_song_data.meta_data == a_song_data.meta_data
                for m1, m2 in zip(j_song_data.measures, a_song_data.measures):
                    assert m1.meta_data == m2.meta_data
                    assert m1.start_time == m2.start_time
                    for n1, n2 in zip(m1.notes, m2.notes):

                        assert type(n1) == type(n2)
                        if isinstance(n1, AdornedNote):

                            assert n1.note.note_number == n2.note.note_number
                            assert n1.note.pitch == n2.note.pitch
                            assert n1.note.fret_number == n2.note.fret_number
                            assert n1.note.string_number == n2.note.string_number
                            assert n1.note.string_tuning == n2.note.string_tuning
                            assert n1.note.start_time == n2.note.start_time
                            assert n1.note.duration == n2.note.duration
                            assert n1.note.dynamic == n2.note.dynamic

                            print(n1.adornment.plucking)
                            print(n2.adornment.plucking)
                            assert n1.adornment.plucking == n2.adornment.plucking
                            assert n1.adornment.fretting == n2.adornment.fretting

                        elif isinstance(n1, Rest):
                            assert n1.note_number == n2.note_number
                            assert n1.start_time == n2.start_time
                            assert n1.duration == n2.duration
            """

        if json_file is None:
            file_name = gp5_file
        else:
            file_name = json_file

        self.add_entries(
            api_song_data=api_song_data,
            file_name=file_name,
            remove_duplicates=remove_duplicates,
            save_feature_files=save_feature_files,
            artist_and_title_from_file_name=artist_and_title_from_file_name,
        )

        return

    def add_entries_from_list_of_json_files(
        self,
        list_of_json_files,
        move_tabs=True,
        remove_duplicates=True,
        save_feature_files=False,
        artist_and_title_from_file_name=True,
    ):
        assert isinstance(list_of_json_files, list), "list_of_json_files is not a list"
        for json_file in list_of_json_files:
            print("Adding measures in %s to database..." % json_file)
            self.add_entries_from_json_file(
                json_file,
                move_tabs=move_tabs,
                remove_duplicates=remove_duplicates,
                save_feature_files=save_feature_files,
                artist_and_title_from_file_name=artist_and_title_from_file_name,
            )

    def add_entries_from_json_file(
        self,
        json_file,
        move_tabs=True,
        remove_duplicates=True,
        save_feature_files=False,
        artist_and_title_from_file_name=True,
    ):

        if move_tabs:
            # move the tab
            if not os.path.isfile(self.json_location + "/" + json_file.split("/")[-1]):
                shutil.move(json_file, self.json_location)
                # update the tab location to be loaded.
                json_file = "json/" + json_file.split("/")[-1]
            else:
                print("File with that name is in database json folder")
                return

        # save a record of the last processed file:
        last_processed_file = open(
            self.save_folder + "/" + "last_processed_file.txt", "w"
        )
        last_processed_file.write(json_file)
        last_processed_file.close()

        if move_tabs:
            api_song_data = self.load_json_file(self.save_folder + "/" + json_file)
        else:
            api_song_data = self.load_json_file(json_file)

        if api_song_data is False:
            print("unable to add entry for %s" % json_file)
            return

        self.add_entries(
            api_song_data=api_song_data,
            file_name=json_file,
            remove_duplicates=remove_duplicates,
            save_feature_files=save_feature_files,
            artist_and_title_from_file_name=artist_and_title_from_file_name,
        )

        return

    def add_entries(
        self,
        api_song_data,
        file_name,
        remove_duplicates=True,
        save_feature_files=False,
        artist_and_title_from_file_name=True,
    ):

        # just a catch for when single Song, not in track format
        # is added as an entry.
        if isinstance(api_song_data, Song):
            api_song_data = [api_song_data]

        assert isinstance(api_song_data, list)

        song_entry_tables = []

        for track in range(0, len(api_song_data)):

            artist = api_song_data[track].meta_data.artist
            if artist == "":
                artist = "unknown"

            song_title = api_song_data[track].meta_data.title

            if artist_and_title_from_file_name:
                # patterns to get artist and title from the file name
                # of tabs downloaded from Ultimate Guitar.
                artist_from_file_name = re.compile("[\S*\s]*-")
                title_from_file_name = re.compile("-\s[\S*\s*].*")

                artist_from_file_name = artist_from_file_name.search(
                    file_name.split("/")[-1]
                )
                song = title_from_file_name.search(file_name)

                if artist_from_file_name is not None:
                    artist = artist_from_file_name.group().replace(" -", "")
                if song is not None:
                    song_title = song.group().replace("- ", "").split(".")[0]

            # remove problematic characters:
            artist = remove_bad_chars.sub("", artist)
            song_title = remove_bad_chars.sub("", song_title)

            # track_id = str(song_title) + '_track_' + str(track)
            track_id = self.track_id(song_title, track)

            song_entry_info = []
            song_entry_info.append(
                [
                    "file.id",
                    "file.location",
                    "artist",
                    "song.title",
                    "track",
                    "measure.number",
                    "complexity",
                    "perceived.difficulty",
                    "unadorned.complexity",
                    "unadorned.perceived.difficulty",
                    "single.note",
                    "single.note.pitch",
                    "single.note.fret.number",
                    "single.note.string.number",
                    "single.note.duration",
                ]
            )

            # Combine tied notes and sort the list back into bars:
            note_list = calculate_tied_note_durations(api_song_data[track])
            notes_in_measure = calculate_bars_from_note_list(
                note_list, api_song_data[track]
            )

            rhy_files = []
            midi_files = []
            mcsv_files = []
            two_note_features = []

            for measure in api_song_data[track].measures:
                measure_number = measure.meta_data.number - 1

                # measure_id = track_id + '_bar_' + str(measure.meta_data.number)
                measure_id = self.measure_id(track_id, measure.meta_data.number)

                if not self.valid_measure(
                    measure=measure, notes_in_measure=notes_in_measure[measure_number]
                ):
                    continue

                single_note = False
                note_pitch = 0
                note_fret_number = -1
                note_string_number = 0
                note_duration = 0
                if len(notes_in_measure[measure_number]) == 1:
                    print("single note measure")
                    single_note = True
                    note_pitch = notes_in_measure[measure_number][0].note.pitch
                    note_fret_number = notes_in_measure[measure_number][
                        0
                    ].note.fret_number
                    note_string_number = notes_in_measure[measure_number][
                        0
                    ].note.string_number
                    note_duration = float(
                        notes_in_measure[measure_number][0].note.duration
                    )

                # Calculate the complexites for the measure:
                complexity_note_list = calculate_grace_note_possitions(
                    notes_in_measure[measure_number]
                )
                measure_complexities = calculate_playing_complexity(
                    complexity_note_list,
                    api_song_data[track],
                    by_bar=[measure_number],
                    weight_set=self.weight_set,
                    unadorned_value=True,
                )

                print(measure_complexities)
                if (
                    measure_complexities.adorned == {}
                    or measure_complexities.adorned is None
                ):
                    print("No complexity could be calculated for %s" % measure_id)
                    continue

                database_file_location = file_name
                # if convert_to_json and json_file is not None:
                #    database_file_location = json_file

                song_entry_info.append(
                    [
                        measure_id,
                        database_file_location,
                        artist,
                        song_title,
                        track,
                        measure.meta_data.number,
                        measure_complexities.adorned[measure.meta_data.number].BGM,
                        measure_complexities.adorned[measure.meta_data.number].EVC,
                        measure_complexities.unadorned[measure.meta_data.number].BGM,
                        measure_complexities.unadorned[measure.meta_data.number].EVC,
                        single_note,
                        note_pitch,
                        note_fret_number,
                        note_string_number,
                        note_duration,
                    ]
                )

                # calculate the RHY file for the measure:
                try:
                    rhy_file = str(
                        calculate_rhy_file_for_measure(
                            measure, rhy_file_name=measure_id + ".rhy"
                        )
                    )
                except ValueError:
                    print("Error making RHY file for %s" % measure_id)
                    continue

                # append the rhy_file to the rhy_file list:
                rhy_files.append(rhy_file)

                # see if the measure only has 2 notes:
                if len(notes_in_measure[measure_number]) == 2:
                    tn_features = feature_analysis.combine_synpy_and_fantastic_features_for_two_notes(
                        measure,
                        notes_in_measure[measure_number],
                        rhy_file,
                        r_data_frame=False,
                        save_table=False,
                    )
                    two_note_features.append(tn_features)

                # calculate the midi file for the measure:
                midi_file = calculate_midi_file_for_measure_note_list(
                    notes_in_measure[measure_number], measure, midi_file_name=measure_id
                )
                mcsv_file = run_melconv(midi_file, midi_file.split(".")[0] + ".csv")

                midi_files.append(midi_file)
                if os.path.isfile(mcsv_file):
                    mcsv_files.append(mcsv_file)

            # Then need to do feature analysis:

            # format the mcsv list to be accepted by FANTASTIC:
            mcvs_formated = []
            for file in mcsv_files:
                mcvs_formated.append(file.split(os.getcwd() + "/")[-1])

            # Load r related things:
            feature_analysis.fantastic_interface.load()

            feature_df = feature_analysis.merge_synpy_and_fantastic_features(
                mcvs_formated,
                rhy_files,
                rhy_table_output="_rhy_features.csv",
                save_location="_all_features.csv",
            )

            # set song_entry_file_location:
            song_entry_file_location = "./" + track_id + ".csv"

            if feature_df is not False:
                song_entry_file = open(song_entry_file_location, "w")
                with song_entry_file:
                    writer = csv.writer(song_entry_file)
                    for row in song_entry_info:
                        writer.writerow(row)

                # merge features into the database:
                db_entry = robjects.r["merge"](
                    feature_analysis.read_in_feature_dataframe(
                        song_entry_file_location
                    ),
                    feature_df,
                )

                # write out the data_base:
                robjects.r["write.table"](
                    x=db_entry, file=song_entry_file_location, sep=",", row_names=False
                )
            else:
                # just write out the header to the song_entry_file_location
                song_entry_file_location = "./" + track_id + ".csv"
                song_entry_file = open(song_entry_file_location, "w")
                with song_entry_file:
                    writer = csv.writer(song_entry_file)
                    # write the header:
                    writer.writerow(self.header)

            # then check for single and two note measures:
            song_entry_file = open(song_entry_file_location, "a+")
            with song_entry_file:
                writer = csv.writer(song_entry_file)
                for row in song_entry_info:
                    if row == [
                        "file.id",
                        "file.location",
                        "artist",
                        "song.title",
                        "track",
                        "measure.number",
                        "complexity",
                        "perceived.difficulty",
                        "unadorned.complexity",
                        "unadorned.perceived.difficulty",
                        "single.note",
                        "single.note.pitch",
                        "single.note.fret.number",
                        "single.note.string.number",
                        "single.note.duration",
                    ]:
                        continue
                    elif row[10] is True:
                        print("single_note")
                        track_id = self.track_id(song_title, row[4])
                        measure_id = self.measure_id(track_id, row[5])
                        print(row[0])

                        # make some dummy fantastic data:
                        dummy_fantastic_data = []
                        for fantastic_feature in [
                            "mean.entropy",
                            "mean.productivity",
                            "mean.Simpsons.D",
                            "mean.Yules.K",
                            "mean.Sichels.S",
                            "mean.Honores.H",
                            "p.range",
                            "p.entropy",
                            "p.std",
                            "i.abs.range",
                            "i.abs.mean",
                            "i.abs.std",
                            "i.mode",
                            "i.entropy",
                            "d.range",
                            "d.median",
                            "d.mode",
                            "d.entropy",
                            "d.eq.trans",
                            "d.half.trans",
                            "d.dotted.trans",
                            "len",
                            "glob.duration",
                            "note.dens",
                            "tonalness",
                            "tonal.clarity",
                            "tonal.spike",
                            "int.cont.grad.mean",
                            "int.cont.grad.std",
                            "int.cont.dir.change",
                            "step.cont.glob.var",
                            "step.cont.glob.dir",
                            "step.cont.loc.var",
                            "mode",
                            "h.contour",
                            "int.cont.glob.dir",
                            "int.contour.class",
                        ]:
                            if fantastic_feature == "len":
                                dummy_fantastic_data.append(1)
                            elif fantastic_feature == "d.mode":
                                dummy_fantastic_data.append(row[-1])
                            elif fantastic_feature == "d.median":
                                dummy_fantastic_data.append(row[-1])
                            else:
                                dummy_fantastic_data.append(0)

                        if row[0] + ".rhy" in rhy_files:
                            print("rhy file exists")
                            synpy_data = (
                                feature_analysis.synpy_interface.compute_features(
                                    row[0] + ".rhy"
                                )[1:]
                            )
                            print(song_entry_info[0])
                            print(row + dummy_fantastic_data + synpy_data)
                            assert len(row + dummy_fantastic_data + synpy_data) == len(
                                self.header
                            )
                            writer.writerow(row + dummy_fantastic_data + synpy_data)
                    else:
                        print("Two note measure...")
                        # get a list of all file.ids of the measures
                        # with 2 notes:
                        two_note_measures = [x[0] for x in two_note_features]
                        if row[0] in two_note_measures:
                            # its a two note measure
                            tn_index = two_note_measures.index(row[0])
                            tn_data = two_note_features[tn_index]
                            # make some dummy fantastic data:
                            dummy_fantastic_data = []
                            for fantastic_feature in [
                                "mean.entropy",
                                "mean.productivity",
                                "mean.Simpsons.D",
                                "mean.Yules.K",
                                "mean.Sichels.S",
                                "mean.Honores.H",
                                "p.range",
                                "p.entropy",
                                "p.std",
                                "i.abs.range",
                                "i.abs.mean",
                                "i.abs.std",
                                "i.mode",
                                "i.entropy",
                                "d.range",
                                "d.median",
                                "d.mode",
                                "d.entropy",
                                "d.eq.trans",
                                "d.half.trans",
                                "d.dotted.trans",
                                "len",
                                "glob.duration",
                                "note.dens",
                                "tonalness",
                                "tonal.clarity",
                                "tonal.spike",
                                "int.cont.grad.mean",
                                "int.cont.grad.std",
                                "int.cont.dir.change",
                                "step.cont.glob.var",
                                "step.cont.glob.dir",
                                "step.cont.loc.var",
                                "mode",
                                "h.contour",
                                "int.cont.glob.dir",
                                "int.contour.class",
                            ]:
                                if fantastic_feature == "p.range":
                                    dummy_fantastic_data.append(tn_data[1])
                                elif fantastic_feature == "p.entropy":
                                    dummy_fantastic_data.append(tn_data[2])
                                elif fantastic_feature == "p.std":
                                    dummy_fantastic_data.append(tn_data[3])
                                elif fantastic_feature == "i.abs.mean":
                                    dummy_fantastic_data.append(tn_data[4])
                                elif fantastic_feature == "i.abs.std":
                                    dummy_fantastic_data.append(tn_data[5])
                                elif fantastic_feature == "i.mode":
                                    dummy_fantastic_data.append(tn_data[6])
                                elif fantastic_feature == "i.entropy":
                                    dummy_fantastic_data.append(tn_data[7])
                                elif fantastic_feature == "d.range":
                                    dummy_fantastic_data.append(tn_data[8])
                                elif fantastic_feature == "d.median":
                                    dummy_fantastic_data.append(tn_data[9])
                                elif fantastic_feature == "d.mode":
                                    dummy_fantastic_data.append(tn_data[10])
                                elif fantastic_feature == "d.entropy":
                                    dummy_fantastic_data.append(tn_data[11])
                                elif fantastic_feature == "len":
                                    dummy_fantastic_data.append(tn_data[12])
                                elif fantastic_feature == "glob.duration":
                                    dummy_fantastic_data.append(tn_data[13])
                                elif fantastic_feature == "note.dens":
                                    dummy_fantastic_data.append(tn_data[14])
                                else:
                                    dummy_fantastic_data.append(0)
                            print(row + dummy_fantastic_data + tn_data[-7:])
                            writer.writerow(row + dummy_fantastic_data + tn_data[-7:])

            # save the song_entry_table location
            song_entry_tables.append(song_entry_file_location)

            if save_feature_files is False:
                # delete all the mid, mcsv and rhy files
                print("Deleting feature files....")
                for fname in midi_files:
                    if os.path.isfile(fname):
                        os.remove(fname)

                for rhy_file in rhy_files:
                    if os.path.isfile(rhy_file):
                        os.remove(rhy_file)

                for mcsv_file in mcsv_files:
                    if os.path.isfile(os.path.basename(mcsv_file)):
                        os.remove(os.path.basename(mcsv_file))
            else:
                if not os.path.isdir(self.save_folder + "/midi_files/" + track_id):
                    os.makedirs(self.save_folder + "/midi_files/" + track_id)

                if not os.path.isdir(self.save_folder + "/rhy_files/" + track_id):
                    os.makedirs(self.save_folder + "/rhy_files/" + track_id)

                if not os.path.isdir(self.save_folder + "/csv_files/" + track_id):
                    os.makedirs(self.save_folder + "/csv_files/" + track_id)

                for fname in midi_files:
                    if os.path.isfile(fname):
                        shutil.move(fname, self.save_folder + "/midi_files/" + track_id)

                for rhy_file in rhy_files:
                    if os.path.isfile(rhy_file):
                        shutil.move(
                            rhy_file, self.save_folder + "/rhy_files/" + track_id
                        )

                for mcsv_file in mcsv_files:
                    if os.path.isfile(os.path.basename(mcsv_file)):
                        shutil.move(
                            os.path.basename(mcsv_file),
                            self.save_folder + "/csv_files/" + track_id,
                        )

        for entry in song_entry_tables:
            self.add_entry(entry, remove_duplicates)
            try:
                shutil.move(entry, self.save_folder + "/raw_entry_tables")
            except:
                shutil.copy2(entry, self.save_folder + "/raw_entry_tables")
                os.remove(entry)

        self.clean_up_extra_temp_files()

        return

    def valid_measure(self, measure, notes_in_measure):

        # Preliminary check to see if the measure
        # can be processed:
        # Measure needs to:
        # -  be monophonic
        if measure.meta_data.monophonic is False:
            print(
                "Measure %s is not monophonic, skipping..." % measure.meta_data.number
            )
            return False

        # - contain notes
        if notes_in_measure == []:
            print("Measure %s is has no notes, skipping..." % measure.meta_data.number)
            return False

        # - have a valid time signature:
        valid_time_sigs = [
            "2/2",
            "3/2",
            "4/2",
            "2/4",
            "3/4",
            "4/4",
            "5/4",
            "6/4",
            "7/4",
            "3/8",
            "5/8",
            "6/8",
            "7/8",
            "9/8",
            "12/8",
            "12/16",
        ]
        valid_time_sigs += list(musiplectics.time_sig_weights().keys())

        if measure.meta_data.time_signature not in set(valid_time_sigs):
            print(
                "Measure %s does not have a valid time signature, skipping..."
                % measure.meta_data.number
            )
            return False

        return True

    def add_entry(self, song_entry_file_location, remove_duplicates=True):
        """
        add database entries for each measure specified in the
        song entry table found at song_entry_file_location
        """
        assert isinstance(song_entry_file_location, str), (
            "%s is not a string" % song_entry_file_location
        )
        assert song_entry_file_location.split(".")[-1] == "csv", (
            "%s is does not have csv file extension" % song_entry_file_location
        )
        assert os.path.isfile(song_entry_file_location), (
            "%s is not a valid file location" % song_entry_file_location
        )

        # load the database for duplicate testing:
        if remove_duplicates:
            self.load()

        duplicate_test = []

        # read in song_entry_file_location
        with open(str(song_entry_file_location)) as song_entry_file:
            song_entry = csv.reader(song_entry_file, delimiter=",")
            line_count = 0
            for entry in song_entry:

                if line_count == 0:
                    line_count += 1
                else:
                    # See if the gpfile exists.
                    if os.path.isfile(
                        self.save_folder + "/" + entry[1]
                    ) or os.path.isfile(entry[1]):

                        # if is does add to the database:
                        unique_id = str(uuid.uuid4())
                        entry[0] = unique_id
                    if remove_duplicates:
                        print("remove duplicates")
                        # check if bar is a duplicate of any
                        # previous bar in the song or an identified
                        # database duplicate:
                        duplicate = False
                        if entry[self.header.index("complexity") :] in duplicate_test:
                            print("duplicate found!")
                            duplicate = True
                            continue

                        # check to see if the bar is a duplicate
                        # in the database:
                        for entry_id in list(self.data.keys()):
                            if (
                                entry[self.header.index("complexity") :]
                                == self.data[entry_id][
                                    self.header.index("complexity") - 1 :
                                ]
                            ):
                                print("duplicate found!")
                                duplicate = True
                                duplicate_test.append(
                                    entry[self.header.index("complexity") :]
                                )

                        if not duplicate:
                            with open(self.data_location, mode="a+") as data_base_file:
                                data_base_updater = csv.writer(data_base_file)
                                data_base_updater.writerow(entry)
                            duplicate_test.append(
                                entry[self.header.index("complexity") :]
                            )
                    else:
                        with open(self.data_location, mode="a+") as data_base_file:
                            data_base_updater = csv.writer(data_base_file)
                            data_base_updater.writerow(entry)

                    line_count += 1

    def consolidate_multiple_entries_from_same_files(self, entry_ids):
        files_to_load = {}
        for entry_id in entry_ids:
            file_location = self.data[entry_id][0]

            if file_location not in files_to_load:
                files_to_load[file_location] = [entry_id]
            else:
                files_to_load[file_location].append(entry_id)
                files_to_load[file_location].sort()

        return files_to_load

    def retrieve_data_form_multiple_entries_from_same_files(
        self, file_location, entry_ids, return_ids=False, process_tied_notes=False
    ):

        return_measures = []

        if self.data is None:
            self.load()

        print("loading default file location:")

        song = self.load_file(self.save_folder + "/" + file_location)

        if song is False:
            print("loading database entry file location:")
            song = self.load_file(file_location)

        if song is False:
            print("could not load song data")
            return return_measures

        track_measures = []
        if process_tied_notes:
            for track in song:
                track_measures.append(
                    calculate_bars_from_note_list(
                        calculate_tied_note_durations(track), track
                    )
                )

        for entry_id in entry_ids:
            entry = self.data.get(entry_id, False)

            if entry:

                track = int(entry[self.header.index("track") - 1])
                measure = int(entry[self.header.index("measure.number") - 1]) - 1
                """
                # Added a check to make sure track numbers and measure
                # number are in the right range:
                if track < 0 or track >= len(song):
                    continue
                if measure < 0 or measure >= len(song[track].measures):
                    continue
                """
                retrieved_measure = song[track].measures[measure]

                if process_tied_notes:
                    # process tied notes:
                    notes_in_measures = track_measures[track][measure]

                    retrieved_measure = Measure(
                        meta_data=song[track].measures[measure].meta_data,
                        start_time=song[track].measures[measure].start_time,
                        notes=notes_in_measures,
                    )

                if return_ids:
                    return_measures.append(
                        # retieved(entry_id, song[track].measures[measure]))
                        retieved(entry_id, retrieved_measure)
                    )

                else:
                    # return_measures.append(song[track].measures[measure])
                    return_measures.append(retrieved_measure)

            else:
                print("No entry found with id: %s" % entry_id)

        return return_measures

    def retrieve_data_from_multiple_entries(self, entry_ids, return_ids=False):
        """
        returns the API data for the database entry with entry_id
        """
        files_to_load = self.consolidate_multiple_entries_from_same_files(entry_ids)

        return_measures = []

        for file_location in files_to_load:
            return_measures += self.retrieve_data_form_multiple_entries_from_same_files(
                file_location, files_to_load[file_location], return_ids=return_ids
            )

        return return_measures

    def retrieve_entry_data(self, entry_id):
        """
        returns the API data for the database entry with entry_id
        """
        try:
            entry = self.data.get(entry_id, False)

            if entry:
                file_location = entry[self.header.index("file.location") - 1]
                track = int(entry[self.header.index("track") - 1])
                measure = int(entry[self.header.index("measure.number") - 1]) - 1

                song = self.load_file(self.save_folder + "/" + file_location)
                if song is False:
                    song = self.load_file(file_location)

                return song[track].measures[measure]
            else:
                print("No entry found with id: %s" % entry_id)
                return None

        except AttributeError as error:
            print(error)
            print("loading data...")
            try:
                self.load()
                entry = self.data.get(entry_id, False)

                if entry:
                    file_location = entry[self.header.index("file.location") - 1]
                    track = int(entry[self.header.index("track") - 1])
                    measure = int(entry[self.header.index("measure.number") - 1]) - 1
                    print(file_location)
                    song = self.load_file(file_location)

                    return song[track].measures[measure]
                else:
                    print("No entry found with id: %s" % entry_id)
                    return None

            except AttributeError as error:
                print(error)
                print("could not load data")
                return None

    def load(self):
        """
        load the database data from self.data_location

        code was based off:
            https://stackoverflow.com/questions/6740918/creating-a-dictionary-from-a-csv-file
        """
        # with open(self.data_location) as f:
        #    csv_list = [[val.strip() for val in r.split(",")]
        #                for r in f.readlines()]

        # strip out the header from the csv file:
        # data = csv_list[1:]
        data = self.load_data_as_lists()[1:]

        # make a dict of entries
        csv_dict = {row[0]: row[1:] for row in data}
        self.data = csv_dict

    def load_data_as_lists(self):
        with open(self.data_location) as f:
            csv_list = [[val.strip() for val in r.split(",")] for r in f.readlines()]

        return csv_list

    def sort(self, complexity_weight=1, difficulty_weight=1, adorned=True, save=True):
        """Sort the database by the huerisitics determined by
        complexity_weight and difficulty_weight

        """
        data = self.load_data_as_lists()
        sorted_data = []

        if complexity_weight == 0 and difficulty_weight == 0:
            print(
                "No sorting needed as complexity weight and difficulty_weight are set to 0"
            )
            return data[1:]

        if (
            self.sorted.adorned == adorned
            and complexity_weight == self.sorted.complexity_weight
            and difficulty_weight == self.sorted.difficulty_weight
        ):
            print("Already sorted!... returning")
            return data[1:]

        print(
            "Sorting database by complexity weight %d, difficulty_weight %d This can take a few minutes!..."
            % (complexity_weight, difficulty_weight)
        )

        if adorned:
            complexity_header = "complexity"
            difficulty_header = "perceived.difficulty"
        else:
            complexity_header = "unadorned.complexity"
            difficulty_header = "unadorned.perceived.difficulty"

        for row in data[1:]:
            sorted_index = 0
            for sorted_row in sorted_data:
                heuristic = calculate_heuristic(
                    float(row[self.header.index(complexity_header)]),
                    float(sorted_row[self.header.index(complexity_header)]),
                    float(row[self.header.index(difficulty_header)]),
                    float(sorted_row[self.header.index(difficulty_header)]),
                    complexity_weight,
                    difficulty_weight,
                )
                if heuristic >= 0:
                    break
                sorted_index += 1
            sorted_data.insert(sorted_index, row)

        if save:
            print("saving the database....")
            with open(self.data_location, mode="w") as database_csv:
                database_writer = csv.writer(
                    database_csv,
                    delimiter=",",
                    quotechar="|",
                    quoting=csv.QUOTE_MINIMAL,
                )
                database_writer.writerow(data[0])
                for row in sorted_data:
                    database_writer.writerow(row)

            with open(
                self.save_folder + "/" + "sorted.txt", mode="w"
            ) as sorted_savefile:
                sorted_savefile.write(str(adorned) + "\n")
                sorted_savefile.write(str(complexity_weight) + "\n")
                sorted_savefile.write(str(difficulty_weight) + "\n")

            # update the sorted flag:
            self.sorted = sorted(adorned, complexity_weight, difficulty_weight)

        return sorted_data

    def subset(
        self,
        complexity_weight=1,
        difficulty_weight=1,
        percentile_range=[0, 100],
        adorned=True,
        artists="all",
        files="all",
        exclude_artists=["none"],
        exclude_files=["none"],
    ):
        """

        Parameters:
        ----------
        percentile_range : list, number
        """

        lower_percentile = min(percentile_range)
        upper_percentile = max(percentile_range)

        if lower_percentile > 0 or upper_percentile < 100:
            # check if the database has been sorted:
            if self.sorted.adorned is None:
                # then sort the database:
                self.sort(complexity_weight, difficulty_weight)

            elif (
                self.sorted.complexity_weight != complexity_weight
                or self.sorted.difficulty_weight != difficulty_weight
                or self.sorted.adorned != adorned
            ):
                # database is sorted wrong:
                # sort the database:
                self.sort(complexity_weight, difficulty_weight)

        # Need to change this to work on row numbers
        subset_database = robjects.r(
            """
            subset.db <- function(database,
                                    lower.percentile=0,
                                    upper.percentile=100,
                                    artists,
                                    files){

                lower.percentile.row <- round(length(database$file.id)/100 * (101-lower.percentile))
                upper.percentile.row <- round(length(database$file.id)/100 * (101-upper.percentile))


                database <- database[upper.percentile.row:lower.percentile.row,]
                database <- database[
                        database$artist %in% artists,
                        ]
                database <- database[
                        database$file.location %in% files,
                        ]
            }
        """
        )

        database_features = feature_analysis.read_in_feature_dataframe(
            self.data_location
        )

        self.load()

        if artists == "all":
            artists = [
                d[self.header.index("artist") - 1] for d in list(self.data.values())
            ]
            artists = list(set(artists))
        elif not isinstance(artists, list):
            artists = [artists]

        if files == "all":
            files = [
                d[self.header.index("file.location") - 1]
                for d in list(self.data.values())
            ]
            files = list(set(files))
        elif not isinstance(files, list):
            files = [files]

        artists = [artist for artist in artists if artist not in exclude_artists]
        files = [file for file in files if file not in exclude_files]

        return subset_database(
            database_features,
            lower_percentile,
            upper_percentile,
            robjects.vectors.StrVector(artists),
            robjects.vectors.StrVector(files),
        )

    def find_most_similar(
        self,
        measure,
        notes_in_measure=[],
        complexity_weight=1,
        difficulty_weight=1,
        **subset_parameters
    ):
        """ """

        print("subset_parameters:", subset_parameters)

        # sort out the subset parameters:
        similarity_threshold = 100 - subset_parameters.get("similarity_threshold", 100)
        percentile_range = subset_parameters.get("percentile_range", [0, 100])
        adorned = subset_parameters.get("adorned", True)
        artists = subset_parameters.get("artists", "all")
        files = subset_parameters.get("files", "all")
        exclude_artists = subset_parameters.get("exclude_artists", ["none"])
        exclude_files = subset_parameters.get("exclude_files", ["none"])

        assert isinstance(measure, Measure)
        assert isinstance(notes_in_measure, list) or isinstance(
            notes_in_measure, AdornedNote
        )

        if notes_in_measure == []:
            notes_in_measure = calculate_tied_note_durations(measure)
        else:
            # if the input is a list make sure they only contain
            # adorned notes:
            if isinstance(notes_in_measure, list):
                for note in notes_in_measure:
                    assert isinstance(note, AdornedNote)
            # if its a single note (as might be the case:)
            # make it a list:
            if isinstance(notes_in_measure, AdornedNote):
                notes_in_measure = [notes_in_measure]

        # Load r related things:
        feature_analysis.fantastic_interface.load()
        if self.get_similarity_features_for_measure(measure, notes_in_measure) is None:
            return []

        measure_id, measure_features = self.get_similarity_features_for_measure(
            measure, notes_in_measure
        )

        mix_features = robjects.r(
            """
                    mix.features <- function(df1, df2){
                    rbind(df1, df2[, names(df1)])
                    }
                """
        )

        get_candidate_set = robjects.r(
            """
                    get.candidate.set <- function(measure.database.df, eucl.stand=TRUE, percent.match=1){

                        if(eucl.stand==TRUE){measure.database.df <- ztransform(measure.database.df)}

                        # get the features from the measure
                        features<-colnames(measure.database.df[,c(-1)])

                        rows <- measure.database.df$file.id[c(-1)]

                        database.df <- measure.database.df[c(-1),features]
                        rownames(database.df) <- rows
                        colnames(database.df) <- features

                        measure.df <- measure.database.df[1,features]
                        rownames(measure.df) <-  measure.database.df[1,1]

                        sim <- apply(database.df, 1, function(x)exp(-dist(rbind(x, measure.df))/length(features)))

                        sim.df <- data.frame(sim)
                        sim.df$file.id <- rownames(sim.df)

                        similarity.range <- max(sim.df$sim) - min(sim.df$sim)
                        out <- as.character(sim.df$file.id[which(sim.df$sim >= max(sim.df$sim)-percent.match*similarity.range/100)])

                        out
                        }
                """
        )

        # subset the database:
        database_features_subset = self.subset(
            complexity_weight=complexity_weight,
            difficulty_weight=difficulty_weight,
            percentile_range=percentile_range,
            adorned=adorned,
            artists=artists,
            files=files,
            exclude_artists=exclude_artists,
            exclude_files=exclude_files,
        )

        df = mix_features(measure_features, database_features_subset)
        """
        note_list = calculate_tied_note_durations(measure)
        single_note = False
        if len(note_list) == 1:
            single_note = True
        """

        print("Finding most similar measures....")
        candidate_set = get_candidate_set(df, True, similarity_threshold)

        self.clean_up_extra_temp_files()

        return candidate_set

    def sort_candidate_set(
        self, candidate_set, complexity_weight, difficulty_weight, adorned=True
    ):
        sorted_candidates = []

        # load the database:
        self.load()
        if adorned:
            complexity_index = self.header.index("complexity") - 1
            difficulty_index = self.header.index("perceived.difficulty") - 1
        else:
            complexity_index = self.header.index("unadorned.complexity") - 1
            difficulty_index = self.header.index("unadorned.perceived.difficulty") - 1

        # sort the candidate ids by the heuristic:
        for candidate_id in candidate_set:
            candidate_entry = self.data.get(candidate_id)

            index = 0
            for sorted_candidate in sorted_candidates:
                heuristic = calculate_heuristic(
                    float(candidate_entry[complexity_index]),
                    float(sorted_candidate.complexity),
                    float(candidate_entry[difficulty_index]),
                    float(sorted_candidate.difficulty),
                    complexity_weight,
                    difficulty_weight,
                )
                if heuristic >= 0:
                    break
                index += 1
            sorted_candidates.insert(
                index,
                candidate(
                    complexity=float(candidate_entry[complexity_index]),
                    difficulty=float(candidate_entry[difficulty_index]),
                    id=candidate_id,
                ),
            )

        return sorted_candidates

    def get_similarity_features_for_measure(self, measure, notes_in_measure=[]):
        """ """

        assert isinstance(measure, Measure)
        if notes_in_measure == []:
            notes_in_measure = calculate_tied_note_durations(measure)
        else:
            for note in notes_in_measure:
                assert isinstance(note, AdornedNote)

        song_title = remove_bad_chars.sub("", measure.meta_data.title)
        measure_id = song_title + "_measure_" + str(measure.meta_data.number)

        if not self.valid_measure(measure=measure, notes_in_measure=notes_in_measure):
            return None

        # calculate the RHY file for the measure:
        rhy_file = str(
            calculate_rhy_file_for_measure(measure, rhy_file_name=measure_id + ".rhy")
        )

        # calculate the midi file for the measure:
        midi_file = calculate_midi_file_for_measure_note_list(
            notes_in_measure, measure, midi_file_name=measure_id
        )

        mcsv_file = run_melconv(midi_file, midi_file.split(".")[0] + ".csv")

        # format the mcsv list to be accepted by FANTASTIC:
        mcvs_formated = mcsv_file.split(os.getcwd() + "/")[-1]

        # Load r related things:
        feature_analysis.fantastic_interface.load()

        feature_df = feature_analysis.merge_synpy_and_fantastic_features(
            [mcvs_formated], [rhy_file], save_table=False
        )

        # work out the information for
        if len(notes_in_measure) == 1:
            print("single note measure")
            # Make a csv file with the synpy features calculated
            feature_analysis.synpy_interface.make_feature_table(
                [rhy_file], output="rhy_features.csv"
            )

            # Make a quick function to read the synpy features
            # into r as a dataframe so it can 'merge' with the
            # fantastic features
            get_synpy_data = robjects.r(
                """
                    synpy.data <- function(file = 'synpy_features.csv' ){
                    data.frame(read.csv(file))
                    }
                """
            )

            single_note_features = robjects.r(
                """
                    single.note.features <- function(measure.id, pitch, fret, string, duration){
                    data.frame('file.id'=measure.id,
                    'single.note.pitch'=pitch,
                    'single.note.fret.number'=fret,
                    'single.note.string.number'=string,
                    single.note.duration=duration,
                    "d.mode"=duration,
                    "d.median"=duration,
                    "len"=1)
                    }
                """
            )

            fantastic_features = single_note_features(
                measure_id,
                notes_in_measure[0].note.pitch,
                notes_in_measure[0].note.fret_number,
                notes_in_measure[0].note.string_number,
                float(notes_in_measure[0].note.duration),
            )
            synpy_features = get_synpy_data("rhy_features.csv")
            feature_df = robjects.r["merge"](fantastic_features, synpy_features)

        if len(notes_in_measure) == 2:
            print("Two note measure")
            feature_df = (
                feature_analysis.combine_synpy_and_fantastic_features_for_two_notes(
                    measure, notes_in_measure, rhy_file, r_data_frame=True
                )
            )

        if os.path.isfile(midi_file):
            os.remove(midi_file)
        if os.path.isfile(rhy_file):
            os.remove(rhy_file)
        if os.path.isfile("rhy_features.csv"):
            os.remove("rhy_features.csv")
        if os.path.isfile(os.path.basename(mcsv_file)):
            os.remove(os.path.basename(mcsv_file))

        return measure_id, feature_df

    def general_virtuosity_threshold(
        self, virtuosity_percentile, complexity_weight, difficulty_weight
    ):
        """ """
        # load the database:
        self.load()

        sorted_adorned_db = self.sort(
            complexity_weight, difficulty_weight, adorned=True, save=False
        )
        sorted_unadorned_db = self.sort(
            complexity_weight, difficulty_weight, adorned=False, save=False
        )

        adorned_percentile_index = round(
            len(sorted_adorned_db) / 100 * (100 - virtuosity_percentile)
        )
        unadorned_percentile_index = round(
            len(sorted_unadorned_db) / 100 * (100 - virtuosity_percentile)
        )

        adorned_threshold = sorted_adorned_db[adorned_percentile_index][
            self.header.index("complexity") : self.header.index("perceived.difficulty")
        ]
        unadorned_threshold = sorted_unadorned_db[unadorned_percentile_index][
            self.header.index("unadorned.complexity") : self.header.index(
                "unadorned.perceived.difficulty"
            )
        ]
        return

    def virtuosity_threshold(
        self,
        complexity_weight,
        difficulty_weight,
        measure=None,
        notes_in_measure=[],
        virtuosity_type="performance",
        virtuosity_percentile=99,
        similarity_threshold=0,
        **other_similarity_parameters
    ):
        """Determine the complexity and perceieved difficulty values
        for the measure to be concidered virtuosic within the context
        of this database, given the level of musical similarity to other
        measures in the database, and the complexity and difficulty weights.

        """

        assert (
            virtuosity_type == "performance" or virtuosity_type == "musical"
        ), "virtuosity_type must be set to 'performance' or 'musical'"
        if virtuosity_type == "performance":
            adorned = True
        elif virtuosity_type == "musical":
            adorned = False

        # sort out the subset parameters:
        percentile_range = other_similarity_parameters.get("percentile_range", [0, 100])
        # adorned = subset_parameters.get('adorned', True)
        artists = other_similarity_parameters.get("artists", "all")
        files = other_similarity_parameters.get("files", "all")
        exclude_artists = other_similarity_parameters.get("exclude_artists", ["none"])
        exclude_files = other_similarity_parameters.get("exclude_files", ["none"])

        self.load()
        most_similar_ids = list(self.data.keys())

        if measure is not None:
            most_similar_ids = self.find_most_similar(
                measure,
                notes_in_measure=notes_in_measure,
                complexity_weight=complexity_weight,
                difficulty_weight=difficulty_weight,
                similarity_threshold=similarity_threshold,
                percentile_range=percentile_range,
                adorned=adorned,
                artists=artists,
                files=files,
                exclude_artists=exclude_artists,
                exclude_files=exclude_files,
            )

        print("sorting...")
        sorted_set = self.sort_candidate_set(
            most_similar_ids, complexity_weight, difficulty_weight, adorned
        )

        if sorted_set == []:
            return None

        print("consolidating...")
        consolidated = cbr.consolidate_same_complexity_difficulty(sorted_set)

        percentile_index = int(
            round(len(consolidated) / 100 * (100 - virtuosity_percentile))
        )

        print(percentile_index)

        # prevent the percentile_index going out of bounds
        if percentile_index >= len(consolidated):
            percentile_index = len(consolidated) - 1

        print(
            "Similarity Matches:",
            len(consolidated),
            "Percentile Index:",
            percentile_index,
        )
        print(
            "Virtuosity Threshold:",
            consolidated[percentile_index].complexity,
            consolidated[percentile_index].difficulty,
        )
        # if percentile_index > 0:
        #    pieces = consolidated[0:percentile_index]
        # else:
        #    pieces = [consolidated[percentile_index]]
        return VirtuosityThreshold(
            float(consolidated[percentile_index].complexity),
            float(consolidated[percentile_index].difficulty),
            consolidated,
        )

    def clean_up_extra_temp_files(self):
        # Clean up extra files....
        print("Cleaning temp files....")
        if os.path.isfile("rhy_features.csv"):
            os.remove("rhy_features.csv")
        if os.path.isfile("_rhy_features.csv"):
            os.remove("_rhy_features.csv")
        if os.path.isfile("_all_features.csv"):
            os.remove("_all_features.csv")

    def produce_report(self, input_file, output_file, **parameters):
        """report measure complexities/difficulties (before/after)
        and list the notes that were modified, the proportion etc.
        Ill also add the virtuosity threshold and a flag to indicate if it was passed.
        Could also save the input parameters too while im at it.

        """

        input_song = guitarpro.parse(input_file)
        input_song = get_functions.get_song_data(input_song)

        output_song = guitarpro.parse(output_file)
        output_song = get_functions.get_song_data(output_song)

        unadorned_input_song = parameters.get("unadorned_input_song", True)

        report_name = (
            self.save_folder
            + "/output/reports/"
            + output_file.split("/")[-1].split(".gp5")[0]
            + "_report"
            + ".csv"
        )

        report_data = []

        total_notes = 0
        total_modified_notes = 0

        total_measures = 0
        total_meaures_passed_virtuosity_threshold = 0

        report_data.append(["input_file:", input_file])
        report_data.append(["output_file:", output_file])

        # write out the input parameters:
        report_data.append(
            ["complexity_weight:", parameters.get("complexity_weight", "")]
        )

        complexity_weight = parameters.get("complexity_weight", "")
        difficulty_weight = parameters.get("difficulty_weight", "")
        gp5_wellformedness = parameters.get("gp5_wellformedness", "")
        virtuosity_percentile = parameters.get("virtuosity_percentile", "")
        virtuosity_similarity_threshold = parameters.get(
            "virtuosity_similarity_threshold", ""
        )
        reflection_loop_limit = parameters.get("reflection_loop_limit", "")
        similarity_threshold_relax_increment = parameters.get(
            "similarity_threshold_relax_increment", ""
        )
        percentile_range_relax_increment = parameters.get(
            "percentile_range_relax_increment", ""
        )
        similarity_threshold_limit = parameters.get("similarity_threshold_limit", "")
        percentile_limit = parameters.get("percentile_limit", "")
        similarity_threshold = parameters.get("similarity_threshold", "")
        percentile_range = parameters.get("percentile_range", "")
        weight_set = parameters.get("weight_set", "RD")

        report_data.append(["complexity_weight:", complexity_weight])
        report_data.append(["difficulty_weight:", difficulty_weight])
        report_data.append(["gp5_wellformedness:", gp5_wellformedness])
        report_data.append(["virtuosity_percentile:", virtuosity_percentile])
        report_data.append(["reflection_loop_limit:", reflection_loop_limit])
        report_data.append(
            [
                "similarity_threshold_relax_increment:",
                similarity_threshold_relax_increment,
            ]
        )
        report_data.append(["percentile_limit:", percentile_limit])
        report_data.append(["similarity_threshold:", similarity_threshold])
        report_data.append(
            [
                "percentile_range:",
                str(percentile_range[0]) + " - " + str(percentile_range[1]),
            ]
        )

        track_count = 0
        for input_track, output_track in zip(input_song, output_song):

            input_song_complexity = calculate_playing_complexity(
                input_track,
                song=input_track,
                by_bar=False,
                weight_set=self.weight_set,
                unadorned_value=unadorned_input_song,
            )

            output_song_complexity = calculate_playing_complexity(
                output_track,
                song=output_track,
                by_bar=False,
                weight_set=self.weight_set,
                unadorned_value=False,
            )

            report_data.append([])
            report_data.append(["source", "complexity", "difficulty"])
            report_data.append(
                [
                    "full_unadorned",
                    input_song_complexity.unadorned.BGM,
                    input_song_complexity.unadorned.EVC,
                ]
            )
            report_data.append(
                [
                    "full_input",
                    input_song_complexity.adorned.BGM,
                    input_song_complexity.adorned.EVC,
                ]
            )
            report_data.append(
                ["full_output", output_song_complexity.BGM, output_song_complexity.EVC]
            )
            report_data.append(
                [
                    "track",
                    "measure_number",
                    "unadorned_complexity",
                    "input_complexity",
                    "output_complexity",
                    "unadorned_difficulty",
                    "input_difficulty",
                    "output_difficulty",
                    "virtuosity_threshold_complexity",
                    "virtuosity_threshold_difficulty",
                    "passed_virtuosity_threshold",
                    "total_notes",
                    "number_modified",
                    "modified_proportion",
                ]
            )

            for input_song, output_song in zip(input_track, output_track):
                input_note_list = calculate_tied_note_durations(input_track)
                input_notes_in_measure = calculate_bars_from_note_list(
                    input_note_list, input_track
                )
                output_note_list = calculate_tied_note_durations(output_track)
                output_notes_in_measure = calculate_bars_from_note_list(
                    output_note_list, output_track
                )

                modified_notes_in_measure = []

                for input_measure, output_measure in zip(
                    input_track.measures, output_track.measures
                ):
                    input_measure_index = input_measure.meta_data.number - 1
                    output_measure_index = output_measure.meta_data.number - 1

                    assert input_measure_index == output_measure_index
                    measure_index = input_measure_index

                    modified_note_count = 0

                    # compare the notes between each measure:
                    for input_note, output_note in zip(
                        input_notes_in_measure[measure_index],
                        output_notes_in_measure[measure_index],
                    ):
                        # check the notes are the same ones:
                        assert (
                            input_note.note.note_number == output_note.note.note_number
                        )
                        assert input_note.note.pitch == output_note.note.pitch
                        assert input_note.note.start_time == output_note.note.start_time

                        # check if they were modified:
                        if input_note != output_note:
                            modified_note_count += 1

                    mod_notes = modified_notes(
                        input_measure.meta_data.number,
                        modified_note_count,
                        modified_note_count
                        / len(input_notes_in_measure[measure_index]),
                    )
                    modified_notes_in_measure.append(mod_notes)

                    # need the virtuosity threshold for the measure:

                    virtuosity_threshold = self.virtuosity_threshold(
                        complexity_weight,
                        difficulty_weight,
                        measure=input_measure,
                        notes_in_measure=input_notes_in_measure[measure_index],
                        virtuosity_type="performance",
                        virtuosity_percentile=virtuosity_percentile,
                        similarity_threshold=virtuosity_similarity_threshold
                        # **other_similarity_parameters
                    )

                    # write out the row:
                    # track,
                    # measure_number,
                    # unadorned complexity,
                    # input_complexity,
                    # output_complexity,
                    # virtuosity_threshold,
                    # passed_virtuosity_threshold,
                    # mod_notes.total_modified,
                    # mod_notes.proportion

                    # Calculate the complexites for the measure:
                    input_complexity_note_list = calculate_grace_note_possitions(
                        input_notes_in_measure[measure_index]
                    )
                    input_song_bar_complexities = calculate_playing_complexity(
                        input_complexity_note_list,
                        input_track,
                        by_bar=[measure_index],
                        weight_set=self.weight_set,
                        unadorned_value=unadorned_input_song,
                    )

                    output_complexity_note_list = calculate_grace_note_possitions(
                        output_notes_in_measure[measure_index]
                    )
                    output_song_bar_complexities = calculate_playing_complexity(
                        output_complexity_note_list,
                        output_track,
                        by_bar=[measure_index],
                        weight_set=self.weight_set,
                        unadorned_value=True,
                    )

                    if (
                        calculate_heuristic(
                            output_song_bar_complexities.adorned[measure_index + 1].BGM,
                            virtuosity_threshold.complexity,
                            output_song_bar_complexities.adorned[measure_index + 1].EVC,
                            virtuosity_threshold.difficulty,
                            complexity_weight,
                            difficulty_weight,
                        )
                        >= 0
                    ):
                        passed_virtuosity_threshold = True
                        total_meaures_passed_virtuosity_threshold += 1
                    else:
                        passed_virtuosity_threshold = False

                    report_data.append(
                        [
                            track_count,
                            measure_index + 1,
                            input_song_bar_complexities.unadorned[
                                measure_index + 1
                            ].BGM,
                            input_song_bar_complexities.unadorned[
                                measure_index + 1
                            ].EVC,
                            input_song_bar_complexities.adorned[measure_index + 1].BGM,
                            input_song_bar_complexities.adorned[measure_index + 1].EVC,
                            output_song_bar_complexities.adorned[measure_index + 1].BGM,
                            output_song_bar_complexities.adorned[measure_index + 1].EVC,
                            virtuosity_threshold.complexity,
                            virtuosity_threshold.difficulty,
                            passed_virtuosity_threshold,
                            len(input_notes_in_measure[measure_index]),
                            mod_notes.total_modified,
                            mod_notes.proportion,
                        ]
                    )

                    total_notes += len(input_notes_in_measure[measure_index])
                    total_modified_notes += mod_notes.total_modified
                    total_measures += 1

            report_data.append(
                [
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "totals:",
                    total_meaures_passed_virtuosity_threshold,
                    total_notes,
                    total_modified_notes,
                    total_modified_notes / total_notes,
                ]
            )
            track_count += 1

        with open(report_name, mode="w") as report_file:
            report_writer = csv.writer(
                report_file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
            )
            for row in report_data:
                report_writer.writerow(row)

        return report_data
