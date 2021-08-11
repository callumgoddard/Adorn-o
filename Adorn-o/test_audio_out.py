from __future__ import division, print_function, absolute_import

import numpy as np
import scipy.io as sio

import guitarpro
from parser.API.calculate_functions import (
    calculate_physical_model_parameters,
    calculate_physical_model_note_structures)
from parser.API import audio_out
from parser.API.get_functions import get_song_data

# Read in the GP5 Test file:
gp5_file = "./gp5files/test_scores/test_physical_model_out.gp5"
gp5song = guitarpro.parse(gp5_file)
api_test_song = get_song_data(gp5song)

test_song = api_test_song[0]

tempo = test_song.measures[0].meta_data.tempo
#
bend_note = test_song.measures[0].notes[0]
slide_note = test_song.measures[0].notes[1]
trill_note1 = test_song.measures[0].notes[2]
trill_note2 = test_song.measures[0].notes[3]
matlab_engine = audio_out.start_matlab()
matlab_engine = audio_out.add_physical_files_to_path(matlab_engine)
"""
note_struct, string_bend, trill, struct_bend = calculate_physical_model_parameters(
    bend_note, tempo, matlab_engine=matlab_engine)

#assert note_struct['bend']['pos'] == matlab.double([[0.0, 3.0, 12.0]])
#assert note_struct['bend']['val'] == matlab.double([[0.0, 100.0, 100.0]])

slide_note_struct, slide_string, trill, slide_struct = calculate_physical_model_parameters(
    slide_note, tempo, previous_note=None, matlab_engine=matlab_engine)

slide_note_struct_w_prev, string, trill, struct = calculate_physical_model_parameters(
    slide_note, tempo, previous_note=bend_note, matlab_engine=matlab_engine)

sio.savemat('note.mat', {'note': slide_note_struct_w_prev, 'string': string})

#audio_data = audio_out.matlab_audio_to_np_array(struct_bend, string_bend,
#                                               matlab_engine)
#audio_out.write_wav_file('bend_test.wav', audio_data, fs=44100)

trill_note1_struct_w_prev, trill_note1_string, trill_note1_trill, trill_note1_struct = calculate_physical_model_parameters(
    trill_note1, tempo, previous_note=slide_note, matlab_engine=matlab_engine)

print(trill_note1_trill)

mel = matlab_engine.python_params_to_WaveGuide([{
    'note':
    slide_note_struct_w_prev,
    "string":
    string
}, {
    'note':
    slide_note_struct_w_prev,
    "string":
    string
}])

audio_out.write_wav_file('decoder_test.wav', np.asarray(mel[0]), fs=44100)

test_notes, tempo = calculate_physical_model_note_structures(
    test_song, matlab_engine=matlab_engine)
test_mel = matlab_engine.python_params_to_WaveGuide(test_notes, tempo)
audio_out.write_matlab_audio(test_mel, 'melody_test.wav')
"""
for file, file_name in zip([
        "./gp5files/test_scores/test_physical_model_out.gp5",
        "./gp5files/Listening-test-mono/c-4string.gp5",
        "./gp5files/Listening-test-mono/r.gp5",
        "./gp5files/Listening-test-mono/h.gp5",
        "./gp5files/Listening-test-mono/tol.gp5",
        "./gp5files/Listening-test-mono/sd.gp5",
        "./gp5files/Listening-test-mono/s.gp5",
        "./gp5files/Listening-test-mono/wdytiw.gp5",
        "./gp5files/Listening-test-mono/sugar-correct.gp5",
        "./gp5files/Listening-test-mono/h-official.gp5"
], [
        'melody_test.wav', 'c-new.wav',
        'r-new.wav', 'h-new.wav',
        'tol-new.wav', 'sd-new.wav', 's-new.wav', 'wdytiw-new.wav',
        'sugar-new.wav', 'h-official-new.wav'
]):

    print(file)
    gp5_file = file
    gp5song = guitarpro.parse(gp5_file)
    api_test_song = get_song_data(gp5song)

    audio_out.api_to_audio(api_test_song[0], file_name, matlab_engine)
    #audio_out.gp5_to_audio(file, file_name, matlab_engine)
