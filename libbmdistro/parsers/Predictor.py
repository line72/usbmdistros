# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import spacy
import libbmdistro.parsers.better_title as BT

class Predictor:
    def __init__(self):
        self.artist_model = spacy.load('artist_model')
        self.album_model = spacy.load('album_model')

    def predict(self, text):
        doc = self.artist_model(text.lower())  # Ensure text is lowercase
        artist_entities = {ent.label_: ent.text for ent in doc.ents}

        doc = self.album_model(text.lower())
        album_entities = {ent.label_: ent.text for ent in doc.ents}

        artist = artist_entities.get('ARTIST')
        album = album_entities.get('ALBUM')

        # Do Some Normalization
        # title case everything (this isn't great,
        #  but we had to lower case stuff for NER
        artist = BT.better_title(artist)
        album = BT.better_title(album)

        # !mwd - if we see s/t (self-titled), rename it to
        #  the name of the artist

        # !mwd - Handle some weirdo unicode

        # !mwd - Handle some special cases
        
        return artist, album
