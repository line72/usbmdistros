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

import random
import argparse
import os
import math
import spacy
from spacy.training.example import Example
import pandas as pd

MAX_ITERATIONS = 20

def create_training_data(df, entity_type):
    print('create_training_data', entity_type)
    training_data = []
    for _, row in df.iterrows():
        text = row['description'].lower()
        entities = []

        e = row[entity_type]
        if e is None or e == '' or isinstance(e, float):
            continue
        
        entity_value = str(row[entity_type]).lower()

        # Find the position of the entity in the text
        entity_start = text.find(entity_value)
        if entity_start != -1:
            entity_end = entity_start + len(entity_value)
            entities.append((entity_start, entity_end, entity_type.upper()))

        if entities:
            training_data.append((text, {"entities": entities}))

    return training_data


def train_ner_model(nlp, ner, training_data, output_model_path):
    for _, annotations in training_data:
        for ent in annotations["entities"]:
            ner.add_label(ent[2])

    # Disable other pipelines
    unaffected_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]

    # Training loop
    with nlp.disable_pipes(*unaffected_pipes):
        optimizer = nlp.begin_training()
        for itn in range(MAX_ITERATIONS):
            random.shuffle(training_data)
            losses = {}
            batches = spacy.util.minibatch(training_data, size=spacy.util.compounding(4.0, 32.0, 1.001))
            for batch in batches:
                examples = []
                for text, annotations in batch:
                    examples.append(Example.from_dict(nlp.make_doc(text), annotations))
                nlp.update(
                    examples,
                    drop=0.5,
                    losses=losses,
                )
            print(f"Iteration {itn} Losses: {losses}")

    # Save the model
    nlp.to_disk(output_model_path)

def model_exists():
    return os.path.exists('artist_model') and \
        os.path.exists('album_model') and \
        os.path.exists('extra_model') and \
        os.path.exists('format_model')
    
def go(args):
    exists = model_exists()
    if exists and not args.update:
        i = input('Model exists. Overwrite [y/N]')
        if i not in ('y', 'Y'):
            sys.exit(0)
    elif not exists and args.update:
        print('Must create initial model first')
        sys.exit(1)

    # Load your dataset
    df = pd.read_csv(args.filename)  # Replace with your dataset path
        
    # Create separate training datasets for artist, album, and extra
    artist_training_data = create_training_data(df, 'artist')
    album_training_data = create_training_data(df, 'album')
    extra_training_data = create_training_data(df, 'extra')
    format_training_data = create_training_data(df, 'format')

    # Train models
    for d, m in ((artist_training_data, 'artist_model'),
              (album_training_data, 'album_model'),
              (format_training_data, 'format_model'),
              (extra_training_data, 'extra_model')):
        if args.update:
            print(f'Adding Training to {m}')
            nlp = spacy.load(m)
            ner = nlp.get_pipe("ner")

        else:
            print(f'Training new data on {m}')
            nlp = spacy.blank('en')
            ner = nlp.add_pipe("ner")
            
        train_ner_model(nlp, ner, d, m)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser('ner-training.py')
    parser.add_argument('filename', metavar = 'training-data.csv')
    parser.add_argument('-u', '--update',
                        help = 'Update model with new training data',
                        action = 'store_true')
    args = parser.parse_args()
    
    go(args)
