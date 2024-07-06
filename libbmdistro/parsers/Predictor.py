# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import spacy
import libbmdistro.parsers.better_title as BT
import libbmdistro.parsers.FormatClassifier as FC

class Predictor:
    def __init__(self):
        self.artist_model = spacy.load('artist_model')
        self.album_model = spacy.load('album_model')
        self.extra_model = spacy.load('extra_model')
        self.format_model = spacy.load('format_model')

    def predict(self, text):
        doc = self.artist_model(text.lower())  # Ensure text is lowercase
        artist_entities = {ent.label_: ent.text for ent in doc.ents}
        artist = artist_entities.get('ARTIST')

        doc = self.album_model(text.lower())
        album_entities = {ent.label_: ent.text for ent in doc.ents}
        album = album_entities.get('ALBUM')

        doc = self.extra_model(text.lower())  # Ensure text is lowercase
        extra_entities = {ent.label_: ent.text for ent in doc.ents}
        extra = extra_entities.get('EXTRA')

        doc = self.format_model(text.lower())  # Ensure text is lowercase
        format_entities = {ent.label_: ent.text for ent in doc.ents}
        format_ = format_entities.get('FORMAT')

        # Do Some Normalization
        # title case everything (this isn't great,
        #  but we had to lower case stuff for NER
        artist = BT.better_title(artist)
        album = BT.better_title(album)

        # !mwd - if we see s/t (self-titled), rename it to
        #  the name of the artist

        # !mwd - Handle some weirdo unicode

        # !mwd - Handle some special cases
        
        return artist, album, extra, FC.classify(format_)
