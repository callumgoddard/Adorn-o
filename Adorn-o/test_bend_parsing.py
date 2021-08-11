import parser
import cbr

gp5_data = parser.song.fromGPfile('./gp5files/test_scores/bend_parsing.gp5')
song_data = parser.API.get_functions.get_song_data(gp5_data)

#print(song_data)

for measure in song_data[0].measures:
    for note in measure.notes:
        print(note.adornment.fretting.modulation)

song_data_json, song_data_dict = parser.API.write_functions.api_to_json(
    song_data)

song_data_from_json = parser.API.get_functions.get_from_JSON(song_data_dict)

for measure_orig, measure_json in zip(song_data[0].measures,
                                      song_data_from_json[0].measures):
    for note_orig, note_json in zip(measure_orig.notes, measure_json.notes):
        assert note_json.adornment.fretting.modulation == note_orig.adornment.fretting.modulation
        assert note_orig == note_json

    unadorned_measure = measure_orig
    adorned_measures = measure_json
    new_measure = cbr.reuse(
        unadorned_measure,
        parser.API.calculate_functions.calculate_tied_note_durations(unadorned_measure),
        adorned_measures,
        complexity_weight=1,
        difficulty_weight=1,
        weight_set='RD',
        gp5_wellformedness=True)

    for note in new_measure.measure.notes:
        print(len(note.adornment.fretting.modulation.bend.points))
        assert len(note.adornment.fretting.modulation.bend.points) >= 2


gp5_data = parser.song.fromGPfile('./gp5files/test_scores/default_bends.gp5')
song_data = parser.API.get_functions.get_song_data(gp5_data)

for measure in song_data[0].measures:
    for note in measure.notes:
        print(note.adornment.fretting.modulation.bend)
