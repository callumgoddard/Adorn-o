from __future__ import division, print_function, absolute_import

# 3rd party imports
import guitarpro

import parser


# updated the gp5_song....
gp5_file_1 = "./gp5files/test_scores/test_write_gp5_1.gp5"
gp5song_1 = guitarpro.parse(gp5_file_1)

gp5_file_2 = "./gp5files/test_scores/test_write_gp5_2.gp5"
gp5song_2 = guitarpro.parse(gp5_file_2)
api_song_2 = parser.API.get_functions.get_song_data(gp5song_2)

parser.API.write_functions.api_to_gp5(api_song_2[0], gp5song_1)

guitarpro.write(gp5song_1, "./gp5files/test_scores/test_write_gp5_1_revised.gp5")


gp5_file = "./gp5files/test_scores/tied_hammer-ons.gp5"
gp5song = guitarpro.parse(gp5_file)
api_song_tied_hammers = parser.API.get_functions.get_song_data(gp5song)


gp5_file = "./gp5files/test_scores/tied_hammer-ons_no_hammer.gp5"
gp5song_no_hammer = guitarpro.parse(gp5_file)
api_no_hammers = parser.API.get_functions.get_song_data(gp5song_no_hammer)

parser.API.write_functions.api_to_gp5(api_song_tied_hammers[0], gp5song_no_hammer)
guitarpro.write(gp5song, "./gp5files/test_scores/tied_hammers_revised.gp5")

gp5_file_2 = "./gp5files/test_scores/test_write_gp5_2.gp5"
gp5song_2 = guitarpro.parse(gp5_file_2)
api_song_json = parser.API.get_functions.get_song_data(gp5song_2)

parser.API.write_functions.api_to_json(api_song_json)
