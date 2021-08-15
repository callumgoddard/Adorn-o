import subprocess
from fractions import Fraction
import os.path
import csv
from math import log, e


import pkg_resources

melconv_location = pkg_resources.resource_filename(__name__, "melconv")

list_head = 0
list_tail = 1

# List of note letters that can be used as is or manipulated
note_letters = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
"""
# Fret number to Natural Harmonic Interval converter:
fret_2_harmonic_interval = {
    1: 'none',
    2: 37,
    3: 31,
    4: 28,
    5: 24,
    6: 34,
    7: 19,
    8: 36,
    9: 28,
    10: 34,
    11: 'none',
    12: 12,
    13: 'none',
    14: 'none',
    15: 34,
    16: 28,
    17: 36,
    18: 'none',
    19: 'none',
    20: 'none',
    21: 'none',
    22: 34,
    23: 'none',
    24: 24
}
"""

# Fret number to Natural Harmonic Interval converter:
# derived from guitar pro harmonic pitches:
fret_2_harmonic_interval = {
    0: "none",
    1: "none",
    2: 37,
    3: 31,
    4: 30,
    5: 24,
    6: 35,
    7: 19,
    8: 36,
    9: 28,
    10: 34,
    11: "none",
    12: 12,
    13: "none",
    14: "none",
    15: 34,
    16: 28,
    17: 36,
    18: "none",
    19: 19,
    20: "none",
    21: "none",
    22: 34,
    23: "none",
    24: 24,
}

# Convert a midi number to a letter


def midinumber2letter(midinumber):
    # info from: https://www.midikits.net/midi_analyser/midi_note_numbers_for_octaves.htm
    return note_letters[midinumber % 12]


# Re-orders the note letters to start at the tonic, and returns a new list
def reorder_note_letters_to_tonic(tonic):

    new_note_letters = []
    for x in range(0, 11):
        letter = (x + note_letters.index(tonic)) % 12
        new_note_letters.append(note_letters[letter])

    return new_note_letters

    # https://en.wikipedia.org/wiki/Dynamics_%28music%29


def midi2hz(midinumber):
    """Return the hz equivalent of the midi number."""
    return 440 * pow(e, ((midinumber - 69) * log(2) / 12))

    # http://newt.phys.unsw.edu.au/jw/notes.html
    # return 440 * pow(2, ((midinumber - 69) / 12))


dynamic = {
    15: "ppp",
    31: "pp",
    33: "pp",
    47: "p",
    49: "p",
    63: "mp",
    64: "mp",
    79: "mf",
    80: "mf",
    95: "f",
    96: "f",
    111: "ff",
    112: "ff",
    126: "fff",
    127: "fff",
}

dynamics_inv = {
    "ppp": 15,
    "pp": 31,
    "p": 47,
    "mp": 63,
    "mf": 79,
    "f": 95,
    "ff": 111,
    "fff": 126,
}

# http://ems.music.uiuc.edu/people/arunc/miranda/intro_doc/node11.htm
dynamic2dB = {
    "ppp": 64.04,
    "pp": 68.07,
    "p": 72.11,
    "mp": 76.15,
    "mf": 80.18,
    "f": 84.22,
    "ff": 88.26,
    "fff": 92.29,
}

# midi instrument Dictionary
midi2BassType = {
    33: "Acoustic Bass",
    34: "Electric Bass (finger)",
    35: "Electric Bass (pick)",
    36: "Fretless Bass",
    37: "Slap Bass 1",
    38: "Slap Bass 2",
    39: "Synth Bass 1",
    40: "Synth Bass 2",
}

pluck2code = {
    "FS": 1,
    "PK": 2,
    "ST": 3,
    "SP": 4,
    "MU": 5,
    "HO": 6,
    "PO": 7,
}

expression2code = {
    "NO": 1,
    "BE": 2,
    "VI": 3,
    "DN": 4,
    "HA": 5,
    "SL": 6,
}

harmonicFret2Ratio = {
    2.1: Fraction(1, 9),
    2.4: Fraction(1, 8),
    2.7: Fraction(1, 7),
    3.2: Fraction(1, 6),
    4: Fraction(1, 5),
    5: Fraction(1, 4),
    5.8: Fraction(2, 7),
    7: Fraction(1, 3),
}

chord = {
    2: "CH2",
    3: "CH3",
    4: "CH4",
}


def run_melconv(midi_file_in, mcsv_out, melconv_loc=melconv_location):
    midi_file_name = os.path.split(midi_file_in)[list_tail].split(".")[list_head]
    mcsv_output_path = os.path.split(mcsv_out)[list_head]
    mcsv_output_file_name = os.path.split(mcsv_out)[list_tail].split(".")[list_head]

    makeFolderPath(os.path.split(mcsv_out)[list_head])

    if mcsv_out:

        if (
            len(os.path.split(mcsv_out)[list_tail].split(".")) is 1
            or os.path.split(mcsv_out)[list_tail].split(".")[1] is not "csv"
        ):
            print(
                "Output not type csv... correcting to " + mcsv_output_file_name + ".csv"
            )

        mcsv_out = mcsv_output_path + "/" + mcsv_output_file_name + ".csv"

    elif not mcsv_output_file_name:
        print("No output mcsv file name specified using midi file name...")
        mcsv_out = mcsv_output_path + "/" + midi_file_name + ".csv"

    # for calling melconv:
    # melconv -s -f csv -i input1.mid
    command = f"{melconv_loc} -f csv -s -i {midi_file_in}"

    """
    if os.getcwd() is "/Users/cg306/repos/virtuobass/virtuobass/parser/":
        command = (
            "./" + melconv_loc + " -f -s csv -i " + midi_file_in
        )  # + " -o " + mcsv_out
    else:
        command = (
            "./parser/" + melconv_loc + " -f csv -s -i " + midi_file_in
        )  # + " -o " + mcsv_out
    """
    subprocess.call(command, shell=True)

    return mcsv_out


# Function that checks a folder path
# and if it doesn't exist creates the folder


def makeFolderPath(path):
    path = path.split("/")
    output_folder = ""
    for folder in path:
        output_folder = output_folder + folder + "/"
    if os.path.isdir(output_folder) is False:
        os.makedirs(output_folder)
    return output_folder


def main():
    print("Utility functions...")
    # run_melconv("melconv", "../test/ref/score.mid", "score.csv")


if __name__ == "__main__":
    main()
