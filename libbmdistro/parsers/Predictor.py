# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import spacy
import joblib
import numpy as np

import libbmdistro.parsers.better_title as BT

class Predictor:
    def __init__(self):
        self.artist_model = spacy.load('artist_model')
        self.album_model = spacy.load('album_model')
        self.extra_model = spacy.load('extra_model')

        self.format_model = joblib.load('categories_model.pkl')
        self.format_encoder = joblib.load('categories_label_encoder.pkl')

    def predict(self, text):
        # Use the NER models to predict artist, album, and extra
        doc = self.artist_model(text.lower())  # Ensure text is lowercase
        artist_entities = {ent.label_: ent.text for ent in doc.ents}
        artist = artist_entities.get('ARTIST')

        doc = self.album_model(text.lower())
        album_entities = {ent.label_: ent.text for ent in doc.ents}
        album = album_entities.get('ALBUM')

        doc = self.extra_model(text.lower())  # Ensure text is lowercase
        extra_entities = {ent.label_: ent.text for ent in doc.ents}
        extra = extra_entities.get('EXTRA')

        # Use the xgboost model to predict the format
        prediction = self.format_model.predict([text])

        # decode the prediction
        prediction = np.round(prediction).astype(int)
        prediction = np.clip(prediction, 0, len(self.format_encoder.classes_) - 1)
    
        decoded_prediction = self.format_encoder.inverse_transform(prediction[:, 0])
        format_ = decoded_prediction[0]
        
        # Do Some Normalization
        # title case everything (this isn't great,
        #  but we had to lower case stuff for NER
        artist = BT.better_title(artist)
        album = BT.better_title(album)

        # !mwd - if we see s/t (self-titled), rename it to
        #  the name of the artist

        # !mwd - Handle some weirdo unicode

        # !mwd - Handle some special cases
        
        return artist, album, extra, format_
