import parser
import guitarpro
import datetime

#


class Case:
    # Init function - song is set to none so that black case can be made when no song is specified
    def __init__(self, song=None, case_id=datetime.datetime.now()):
        # set case id
        # Which is actually the bar number...
        self.id = case_id
        # check to see what format the song is in
        # if it is a list - this is song data and process the list
        # if it is a guitarpro.base.Song then this needs to have the song data extracted
        if type(song) == list:
            self.song = None
            # create case from song data
            self.fromSongData(song)

        elif type(song) == guitarpro.Song:
            self.song = song
            self.fromSong(song)
        else:
            self.song = None
            self.songdata = None

    # Fills in the case information from songdata format
    def fromSongData(self, songdata):
        # the musical information is split from the meta data
        self.songdata = []
        rownum = 0
        for row in songdata:
            if row[0] == 'id':
                self.id = row[1]
            elif row[0] == 'gpfile':
                self.gpfile = row[1]
            elif row[0] == 'title':
                self.title = row[1]
            elif row[0] == 'subtitle':
                self.subtitle = row[1]
            elif row[0] == 'artist':
                self.artist = row[1]
            elif row[0] == 'album':
                self.album = row[1]
            elif row[0] == 'composer':
                self.composer = row[1]
            elif row[0] == 'transcribed by':
                self.transcriber = row[1]
            else:
                self.songdata.append(row)
            rownum += 1

        # make song data..

        return self

        # fills in case information from song format
    def fromSong(self, song):
        songdata = parser.song.getSongData(song)
        self.fromSongData(songdata)
        return self

    def save(self, output_folder):
        # make a file path from self.id and folder
        # write out the song
        self.gpfile = parser.song.writeToGPfile(self.song, self.SongID(), output_folder)

        # write out the song-data
        # first combine the metadata with songdata:
        savedata = self.combineMetaAndSongData()

        # then write to csv file
        parser.songdata.writeToCSV(savedata, output_folder + "/" + self.SongID() + ".csv")

    def toMidi(self, output_folder):
        # make a song id
        song_id = self.SongID()
        # write the midi data using the parser module
        parser.songdata.toMidi(self.songdata, song_id, output_folder)
        #parser.utilities.run_melconv(m, mcsv_out='mcsv/', melconv_loc="melconv")

    # def midi2mcsv(self, midifolder):
        #parser.utilities.run_melconv(midi_file_in, mcsv_out, melconv_loc="melconv")

    def toRhy(self, output_folder):
        # make a song id
        song_id = self.SongID()
        # write the output to a Rhy file
        parser.songdata.toRhy(self.songdata, song_id, output_folder)

    def SongID(self):
        # make a song id using the track title (with spaces replaced with dashes and case id:
        title_split = self.title.split(" ")
        title_no_spaces = ''
        word_count = 0
        for word in title_split:
            if word_count == 0:
                title_no_spaces = word
            else:
                title_no_spaces = title_no_spaces + '-' + word
            word_count += 1
        song_id = title_no_spaces + "_" + str(self.id)
        return song_id

    def combineMetaAndSongData(self):
        savedata = []
        savedata.append(["id", self.id])
        savedata.append(["title", self.title])
        savedata.append(["subtitle", self.subtitle])
        savedata.append(["gpfile", self.gpfile])
        savedata.append(["artist", self.artist])
        savedata.append(["album", self.album])
        savedata.append(["composer", self.composer])
        savedata.append(["transcriber", self.transcriber])
        for row in self.songdata:
            savedata.append(row)
        return savedata
