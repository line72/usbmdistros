# BMDistro Training

I have switched from manual parsing to using various machine learning
models to parse the results. At this point, I am using two different
models:

* NER (Named Entity Recognition) 
* xgboost + sklearn

NER is being used for basic parsing of the artist, album, and extra
information. This machine learning algorithm works pretty well at
identifying patters on how to parse.

At this pint, I have the NER create a separate model with different
predictions for each field, as I have found this to be more reliable.

However, NER requires the prediction text to exist in the input. This
is good for random text that it has never seen before, but is terrible
for classiflying the format into Vinyl, Cassette, and CD. Therefore,
for classification, I am using xgboost + scikit-learn.

## Creating the Training Data

In the `data/` directory, I have samples from each of the
distros. These samples have been currated and validated to have
correct data. These all end in `-sample.csv`.

I am combining these sample csv into a single `all.csv`. This can be
used to train all the models.

### NER Prediction Model

To create the training data, first you need to run the `NER` model:

```
./ner-training.py data/all.csv
```

Note, it is possible to add data to the model without re-training the
entire model:

```
./ner-training.py --update data/new.csv
```

I am only running 20 iterations. This _seems_ to be enough to converge
and fit the data without overfitting it, but it might need some
tweaking.

This will output 3 models:

- `artist_model/`
- `album_model/`
- `extra_model/`

### Classification Model

To create the classification model:

```
./category-training.py data/all.csv
```

This can also be updated with new data without re-training the entire
model:

```
./category-training.py --update data/new.csv
```

This will output a single model and its labels:

* `categories_model.pkl`
* `categories_label_encoder.pkl`

## Testing the Data

To test predictions, you can run the `test-predict.py` with a sample
CSV. I have created some sample .csv files for each distro with
verified data in the `data/` directory. These end in `-validation.csv`

```
./test-predict.py data/stovokor-validation.csv
```

This will output a ✅ for a match, a ❌ for an incorrect match, and a
‼️ if the model is unable to predict. These are good guidelines for
adding more similar data to the samples.

In some cases a ‼️ is exptected. This is because during the NER
training, if a product isn't a music product (t-shirt, PIN, poster),
then it won't have a valid artist and album, so we put a `?` as the
prediction result. 
