#!/usr/bin/env python3
#
# This is a second attempt, using : Named Entity Recognition (NER)
#
# NER can help identify entities like artist names, album names, and
# formats in a text.  Libraries like SpaCy provide pre-trained models
# that can be fine-tuned for your specific task.
#
# https://chatgpt.com/c/92dc6dc3-5001-4e5e-8c5a-213dcb3831c7
#
# This creates 3 models:
#  artist_model :: Artist
#  album_model :: Album
#  extra_model :: Extra Information
#
# This takes a CSV file and test predictions
#  printing out the confidence score and seeing
#  if it matches the CSV answers

import argparse
import os

import better_title as BT

import pandas as pd
import numpy as np

import joblib

import spacy
from spacy.tokens import Token
from spacy.language import Language
from scipy.special import softmax

# !mwd - I was trying to get a confidence value
#  during prediction. spacy's NER model doesn't support
#  this, but ChatGPT was trying to help me access internals
# I could not get this to work.
#
# # Custom pipeline component factory to add NER scores
# def create_ner_score_component(nlp, name):
#     @Language.component("add_ner_scores_" + name)
#     def add_ner_scores(doc):
#         # Get the NER component and its model
#         ner = nlp.get_pipe("ner")
#         model = ner.model

#         # Extract the logits for each token in the document
#         for i, token in enumerate(doc):
#             doc_tensor = doc.to_array([token.i for token in doc])
#             logits = model.predict([doc_tensor])[0]
#             token_logit = logits[i]

#             # Apply softmax to get probabilities
#             probabilities = softmax(token_logit)
#             token._.set("ner_score", max(probabilities))
        
#         return doc

#     return add_ner_scores

# # Function to calculate confidence scores
# def get_confidence_scores(doc):
#     entity_scores = []

#     for ent in doc.ents:
#         token_scores = [token._.get("ner_score") for token in ent]
#         entity_score = np.mean(token_scores)
#         entity_scores.append((ent.label_, ent.text, entity_score))

#     return entity_scores

# # Function to predict using the fine-tuned model and get confidence scores
# def predict_with_confidence(nlp, text, v):
#     doc = nlp(text.lower())  # Ensure text is lowercase
#     confidence_scores = get_confidence_scores(doc)
#     entities = {ent[0]: (ent[1], ent[2]) for ent in confidence_scores}
#     return entities.get(v)

def predict(nlp, text, v):
    doc = nlp(text.lower())
    entities = {ent.label_: ent.text for ent in doc.ents}

    e = entities.get(v)
    if e:
        return BT.better_title(str(e))
    return None

def predict_category(pipeline, format_encoder, text):
    prediction = pipeline.predict([text])

    # decode the prediction
    prediction = np.round(prediction).astype(int)
    prediction = np.clip(prediction, 0, len(format_encoder.classes_) - 1)
    
    decoded_prediction = format_encoder.inverse_transform(prediction[:, 0])
    
    return decoded_prediction[0]

def go(args):
    # load our artist and album model
    artist_model = spacy.load("artist_model")
    album_model = spacy.load("album_model")

    # load our categories model
    categories_model = joblib.load('categories_model.pkl')
    format_encoder = joblib.load('categories_label_encoder.pkl')

    # # Register the extension attribute
    # Token.set_extension("ner_score", default=0.0, force=True)

    # # Add the component to the pipeline
    # # !mwd - this is some hacky shit. Our add_ner_score needs access
    # #  to our model, but we can only pass in a component functino
    # #  via a name. Therefore, we create two functions on the fly
    # #  and register with (using @Language.component) with the name
    # #  add_ner_scores_xxx
    # # Here we hold on to a reference to those functions
    # f1 = create_ner_score_component(artist_model, "artist")
    # f2 = create_ner_score_component(album_model, "album")
    
    # artist_model.add_pipe('add_ner_scores_artist', after="ner")
    # album_model.add_pipe('add_ner_scores_album', after="ner")

    df = pd.read_csv(args.filename)
    for _, row in df.iterrows():
        predicted_artist = predict(artist_model, row['description'], 'ARTIST')
        predicted_album = predict(album_model, row['description'], 'ALBUM')
        predicted_category = predict_category(categories_model, format_encoder, row['description'])

        art = str(row['artist'])
        alb = str(row['album'])
        cat = str(row['format'])

        print(f"🤜 {row['description']}")
        if predicted_artist:
            (matched, op, ismatch) = ('✅','=', True) if predicted_artist.lower() == art.lower() else ('❌','≠', False)
            print(f"  {matched} Artist: prediction: |{predicted_artist}| {op} |{art}|")
        else:
            print(f"  ‼️  Unable to predict Artist {art} from {row['description']}")
            
        if predicted_album:
            (matched, op, ismatch) = ('✅','=', True) if predicted_album.lower() == alb.lower() else ('❌','≠', False)
            print(f"  {matched} Album: predicted: |{predicted_album}| {op} |{alb}|")
        else:
            print(f"  ‼️  Unable to predict Album {alb} from {row['description']}")

        if predicted_category:
            (matched, op, ismatch) = ('✅','=', True) if predicted_category.lower() == cat.lower() else ('❌','≠', False)
            print(f"  {matched} Category: prediction: |{predicted_category}| {op} |{cat}|")
        else:
            print(f"  ‼️  Unable to predict Category {cat} from {row['description']}")
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser('test-predict.py')
    parser.add_argument('filename', metavar = 'data.csv')
    args = parser.parse_args()

    go(args)
