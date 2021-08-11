# Local Application Imports
import parser

gp5_data = parser.song.fromGPfile(
    './gp5files/test_scores/test_dynamic_values.gp5')
song_data = parser.API.get_functions.get_song_data(gp5_data)

note_count = 0
for note, dynamic in zip(
        parser.API.calculate_functions.calculate_tied_note_durations(
            song_data[0]),
    [
        'ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff', 'ppp', 'pp', 'p', 'mp',
        'mf', 'f', 'ff', 'fff', 'ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff'
    ]):
    assert note.note.dynamic[0] == dynamic
    print()
    note_count += 1
    print(note_count)
