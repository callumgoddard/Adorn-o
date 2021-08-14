

import numpy as np
import scipy.io.wavfile
import matlab.engine

import guitarpro

from parser.API.calculate_functions import (
    calculate_physical_model_note_structures)
from parser.API.get_functions import get_song_data


def gp5_to_audio(gp5_file, file_name, matlab_engine, fs=44100.00):
    gp5song = guitarpro.parse(gp5_file)
    api_test_song = get_song_data(gp5song)

    track_number = 0
    for track in api_test_song:
        file_name = (file_name.split('.wav')[0] + '_track_' + str(track_number)
                     + '.wav')
        api_to_audio(track, file_name, matlab_engine, fs)
        track_number += 1


def api_to_audio(api_song, file_name, matlab_engine, fs=44100.00):
    notes, pause_time = calculate_physical_model_note_structures(
        api_song, matlab_engine=matlab_engine)
    melody = matlab_engine.python_params_to_WaveGuide(notes, fs, pause_time)
    write_matlab_audio(melody, file_name, fs)
    return


def matlab_audio_to_np_array(matlab_audio):

    return np.asarray(matlab_audio[0])


def start_matlab():
    return matlab.engine.start_matlab()


def add_physical_files_to_path(matlab_engine,
                               path='bass_guitar_waveguide_model'):
    """Requires: https://github.com/callumgoddard/bass_guitar_waveguide_model to be
    added to the python working directory"""
    p = matlab_engine.genpath(path)
    matlab_engine.addpath(p)
    return matlab_engine


def write_wav_file(file_name, audio_data, fs=44100.00):
    """Write out audio from a np array to a wavfile

    """
    assert isinstance(file_name, str)
    if file_name.find("wav") == -1:
        file_name = file_name + '.wav'
    print(file_name)
    scipy.io.wavfile.write(file_name, fs, audio_data)


def bass_guitar_decoder(notes, strings, tempo, matlab_engine):

    melody = []
    for note, string in zip(notes, strings):
        melody.append({'note': note, "string": string})

    decoded_melody = matlab_engine.python_params_to_WaveGuide(melody, tempo)

    return decoded_melody


def write_matlab_audio(m_audio, file_name, fs=44100.00):

    audio_data = matlab_audio_to_np_array(m_audio)
    write_wav_file(file_name, audio_data, fs)
