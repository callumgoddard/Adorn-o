from fractions import Fraction

# Local Application Imports
import feature_analysis
import parser

# read in the guitar pro files

grade_0 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade0', filetype='gp5')
grade_1 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade1', filetype='gp5')
grade_2 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade2', filetype='gp5')
grade_3 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade3', filetype='gp5')
grade_4 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade4', filetype='gp5')
grade_5 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade5', filetype='gp5')
grade_6 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade6', filetype='gp5')
grade_7 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade7', filetype='gp5')
grade_8 = feature_analysis.list_all_files_in_folder(
    './gp5files/GradePieces/Grade8', filetype='gp5')
percieved_difficulty = feature_analysis.list_all_files_in_folder(
    './gp5files/Listening-test-mono', filetype='gp5')
percieved_difficulty.remove('./gp5files/Listening-test-mono/mmbs.gp5')
percieved_difficulty.remove('./gp5files/Listening-test-mono/h.gp5')
# percieved_difficulty.remove('./gp5files/Listening-test-mono/sugar-correct.gp5')

for gp5filename in percieved_difficulty:
    print(gp5filename)
    gp5_data = parser.song.fromGPfile(gp5filename)
    song_data = parser.API.get_functions.get_song_data(gp5_data)
    # to account for my new list output from get_song_data()
    song_data = song_data[0]
    if gp5filename in [
            './gp5files/Listening-test-mono/tol.gp5',
            './gp5files/Listening-test-mono/wdytiw.gp5',
            './gp5files/Listening-test-mono/r.gp5',
            './gp5files/Listening-test-mono/h-official.gp5',
            './gp5files/Listening-test-mono/s.gp5'
    ]:
        for note in parser.API.calculate_functions.calculate_tied_note_durations(
                song_data):
            assert note.note.dynamic[0] == 'mf'
    if gp5filename == './gp5files/Listening-test-mono/sd.gp5':
        for note in parser.API.calculate_functions.calculate_tied_note_durations(
                song_data):
            if note.adornment.fretting.modification.type != 'dead-note':
                if note.adornment.plucking.accent and note.note.string_number == 1:
                    assert note.note.dynamic[0] == 'mp'
                else:
                    assert note.note.dynamic[0] == 'mf'

    if gp5filename == './gp5files/Listening-test-mono/c.gp5':
        for note in parser.API.calculate_functions.calculate_tied_note_durations(
                song_data):
            if note.adornment.plucking.accent:
                assert note.note.dynamic[0] == 'mp'

for gp5filename in grade_0 + grade_1 + grade_2 + grade_3 + grade_4:
    print(gp5filename)
    gp5_data = parser.song.fromGPfile(gp5filename)
    song_data = parser.API.get_functions.get_song_data(gp5_data)
    # to account for my new list output from get_song_data()
    song_data = song_data[0]
    for note in parser.API.calculate_functions.calculate_tied_note_durations(
            song_data):
        if './gp5files/GradePieces/Grade2/Comfortably Numb.gp5' == gp5filename:
            assert note.note.dynamic[0] == 'mp'
        elif './gp5files/GradePieces/Grade0/Blitzkreig Bop.gp5' == gp5filename:
            assert note.note.dynamic[0] == 'f'
        elif "./gp5files/GradePieces/Grade1/I Believe I'll Dust My Broom.gp5" == gp5filename:
            assert note.note.dynamic[0] == 'mf' or note.note.dynamic[0] == 'mp'
        elif "./gp5files/GradePieces/Grade3/All Day and All of the Night.gp5" == gp5filename:
            assert (note.note.dynamic[0] == 'mf' or note.note.dynamic[0] == 'f'
                    or note.note.dynamic[0] == 'ff')
        elif './gp5files/GradePieces/Grade4/Everyday Is Like Sunday-no-repeats.gp5' == gp5filename:
            assert (note.note.dynamic[0] == 'mf'
                    or note.note.dynamic[0] == 'f')
        elif gp5filename in [
                './gp5files/GradePieces/Grade0/Folsom Prison Blues-no-repeats.gp5',
                './gp5files/GradePieces/Grade2/Need You Tonight.gp5',
                "./gp5files/GradePieces/Grade3/All Day and All of the Night.gp5"
        ]:
            assert note.note.dynamic[0] == 'mf'
        else:
            continue

gp5filename = "./gp5files/GradePieces/Grade1/Shakin' All Over.gp5"
print(gp5filename)
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]
dynamic_check = ['mf', 'f']
stacatto_count = 0
for note in parser.API.calculate_functions.calculate_tied_note_durations(
        song_data):
    if note.adornment.fretting.accent:
        assert note.note.dynamic[0] == dynamic_check[stacatto_count]
        stacatto_count += 1

gp5filename = "./gp5files/GradePieces/Grade3/Addicted To Love-no-repeats.gp5"
print(gp5filename)
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]
for note in parser.API.calculate_functions.calculate_tied_note_durations(
        song_data):
    if note.adornment.fretting.accent or note.adornment.plucking.accent:
        assert note.note.dynamic[0] == 'f'

gp5filename = "./gp5files/GradePieces/Grade4/Would-no-repeats.gp5"
print(gp5filename)
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]

accent_count = 0
for note in parser.API.calculate_functions.calculate_tied_note_durations(
        song_data):
    if note.adornment.plucking.accent:
        if accent_count < 12:
            assert note.note.dynamic[0] == 'f'
        else:
            assert note.note.dynamic[0] == 'ff'
        accent_count += 1

for gp5filename in [
        "./gp5files/GradePieces/Grade5/I Get High On You-no-repeats.gp5",
        "./gp5files/GradePieces/Grade5/My Generation-no-repeats.gp5",
        "./gp5files/GradePieces/Grade6/Won't Get Fooled Again.gp5"
]:
    print(gp5filename)
    gp5_data = parser.song.fromGPfile(gp5filename)
    song_data = parser.API.get_functions.get_song_data(gp5_data)
    # to account for my new list output from get_song_data()
    song_data = song_data[0]
    for note in parser.API.calculate_functions.calculate_tied_note_durations(
            song_data):

        if not note.adornment.plucking.accent and not note.adornment.plucking.accent:
            check_dynamic = note.note.dynamic[0]
        else:
            print(gp5filename)
            print(note)
            assert note.note.dynamic[0] == check_dynamic

gp5filename = "./gp5files/GradePieces/Grade6/Scratch Your Name-no-repeats.gp5"
print(gp5filename)
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]
for note in parser.API.calculate_functions.calculate_tied_note_durations(
        song_data):
    if not note.adornment.plucking.accent and not note.adornment.plucking.accent:
        check_dynamic = note.note.dynamic[0]
    else:
        if note.note.start_time == 28:
            check_dynamic = 'ff'
            assert note.note.dynamic[0] == check_dynamic
        elif note.note.start_time == 76 or note.note.start_time == 80:
            check_dynamic = 'mf'
            assert note.note.dynamic[0] == check_dynamic
        elif note.note.start_time == Fraction(
                623, 8) or note.note.start_time == Fraction(655, 8):
            check_dynamic = 'f'
            assert note.note.dynamic[0] == check_dynamic

        else:
            assert note.note.dynamic[0] == check_dynamic

gp5filename = "./gp5files/GradePieces/Grade7/Hysteria-no-repeats.gp5"
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]
assert parser.API.calculate_functions.calculate_tied_note_durations(song_data)[
    -1].note.dynamic[0] == 'f'

gp5filename = "./gp5files/GradePieces/Grade7/The Sun Goes Down (Living it Up)-no-repeats.gp5"
print(gp5filename)
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]
for note in parser.API.calculate_functions.calculate_tied_note_durations(
        song_data):
    if not note.adornment.plucking.accent and not note.adornment.plucking.accent:
        check_dynamic = note.note.dynamic[0]
    else:
        if note.note.start_time == Fraction(985, 16):
            check_dynamic = 'f'
            assert note.note.dynamic[0] == check_dynamic
        else:
            assert note.note.dynamic[0] == check_dynamic

gp5filename = "./gp5files/GradePieces/Grade8/600-no-repeats.gp5"
print(gp5filename)
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]
for note in parser.API.calculate_functions.calculate_tied_note_durations(
        song_data):
    if not note.adornment.plucking.accent and not note.adornment.plucking.accent:
        check_dynamic = note.note.dynamic[0]
    else:
        print(note)
        if (note.note.start_time == Fraction(14, 1)
                or note.note.start_time == Fraction(37, 4)
                or note.note.start_time == Fraction(273, 8)
                or note.note.start_time == Fraction(513, 8)):
            check_dynamic = 'mf'
            assert note.note.dynamic[0] == check_dynamic
        elif note.note.start_time == Fraction(449, 8):
            check_dynamic = 'ff'
            assert note.note.dynamic[0] == check_dynamic
        elif note.note.start_time == Fraction(481, 8):
            check_dynamic = 'f'
            assert note.note.dynamic[0] == check_dynamic
        else:
            assert note.note.dynamic[0] == check_dynamic

gp5filename = "./gp5files/GradePieces/Grade8/Love Games-no-repeats.gp5"
print(gp5filename)
gp5_data = parser.song.fromGPfile(gp5filename)
song_data = parser.API.get_functions.get_song_data(gp5_data)
# to account for my new list output from get_song_data()
song_data = song_data[0]
for note in parser.API.calculate_functions.calculate_tied_note_durations(
        song_data):
    if not note.adornment.plucking.accent and not note.adornment.plucking.accent:
        check_dynamic = note.note.dynamic[0]
    else:
        assert note.note.dynamic[0] == check_dynamic
