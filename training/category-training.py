#!/usr/bin/env python3
#
# This is classification algorithm to try to figure out
#  the correct format (vinyl, cassette, cd)
#
# https://chatgpt.com/c/92dc6dc3-5001-4e5e-8c5a-213dcb3831c7
#
# This creates 1 model for the format

import argparse
import os

import pandas as pd
import numpy as np
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import classification_report
from sklearn.decomposition import TruncatedSVD
import xgboost as xgb

def load_data(fname):
    df = pd.read_csv(fname)
    return df

def xgboost(format_encoder, x_train, y_train, x_test, y_test, y):
    # Create a pipeline with TF-IDF and XGBoost
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('svd', TruncatedSVD(n_components=100)),  # Reduce dimensions to 100
        ('clf', MultiOutputRegressor(xgb.XGBRegressor(objective='reg:squarederror', eval_metric='mae', verbosity=0))),
    ])

    # Train the model
    pipeline.fit(x_train, y_train)

    # Predict the test set
    y_pred = pipeline.predict(x_test)
    y_pred = np.round(y_pred).astype(int)  # Convert predictions to integers


    # Clamp predictions to the range of encoded labels
    y_pred[:, 0] = np.clip(y_pred[:, 0], 0, len(format_encoder.classes_) - 1)
    
    # Decode the predictions
    y_test_decoded = y_test.copy()
    y_pred_decoded = y_test.copy()
    y_test_decoded['format'] = format_encoder.inverse_transform(y_test['format_encoded'])
    y_pred_decoded['format'] = format_encoder.inverse_transform(y_pred[:, 0])

    # Generate classification reports for each output field
    for col in ['format']:
        print(f"Classification Report for {col}:")
        print(classification_report(y_test_decoded[col], y_pred_decoded[col]))
        print("\n")

    return pipeline

def save_model(pipeline, filename):
    joblib.dump(pipeline, filename)

def save_label_encoder(encoder, filename):
    joblib.dump(encoder, filename)

def load_model(filename):
    return joblib.load(filename)

def update_model(existing_pipeline, new_data, format_encoder):
    old_x_train = existing_pipeline.named_steps['tfidf'].inverse_transform(
        existing_pipeline.named_steps['svd'].inverse_transform(
            existing_pipeline.named_steps['clf'].estimators_[0]._Booster._data)
    )
    old_y_train = existing_pipeline.named_steps['clf'].estimators_[0]._y
    x_train_combined = np.concatenate((old_x_train, new_data['description']))
    y_train_combined = np.concatenate((old_y_train, new_data['format_encoded']))
    new_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('svd', TruncatedSVD(n_components=100)),
        ('clf', MultiOutputRegressor(xgb.XGBRegressor(objective='reg:squarederror', eval_metric='mae', verbosity=0))),
    ])
    new_pipeline.fit(x_train_combined, y_train_combined)
    return new_pipeline

def go(args):
    df = load_data(args.filename)
    
    format_encoder = LabelEncoder()
    df['format_encoded'] = format_encoder.fit_transform(df['format'])
    
    # Split data into training and test sets
    x = df['description']
    y = df[['format_encoded']]
    
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    if args.update:
        existing_pipeline = load_model('categories_model.pkl')
        updated_pipeline = update_model(existing_pipeline, df, format_encoder)
        save_model(updated_pipeline, 'categories_model.pkl')
        save_label_encoder(format_encoder, 'categories_label_encoder.pkl')
    else:
        pipeline = xgboost(format_encoder, x_train, y_train, x_test, y_test, y)
        save_model(pipeline, 'categories_model.pkl')
        save_label_encoder(format_encoder, 'categories_label_encoder.pkl')
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser('category-training.py')
    parser.add_argument('filename', metavar = 'training-data.csv')
    parser.add_argument('-u', '--update',
                        help = 'Update model with new training data',
                        action = 'store_true')
    args = parser.parse_args()
    
    go(args)
