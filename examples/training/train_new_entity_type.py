#!/usr/bin/env python
# coding: utf8
"""
Example of training an additional entity type

This script shows how to add a new entity type to an existing pre-trained NER
model. To keep the example short and simple, only four sentences are provided
as examples. In practice, you'll need many more — a few hundred would be a
good start. You will also likely need to mix in examples of other entity
types, which might be obtained by running the entity recognizer over unlabelled
sentences, and adding their annotations to the training set.

The actual training is performed by looping over the examples, and calling
`nlp.entity.update()`. The `update()` method steps through the words of the
input. At each word, it makes a prediction. It then consults the annotations
provided on the GoldParse instance, to see whether it was right. If it was
wrong, it adjusts its weights so that the correct action will score higher
next time.

After training your model, you can save it to a directory. We recommend
wrapping models as Python packages, for ease of deployment.

For more details, see the documentation:
* Training the Named Entity Recognizer: https://spacy.io/docs/usage/train-ner
* Saving and loading models: https://spacy.io/docs/usage/saving-loading

Developed for: spaCy 1.7.6
Last updated for: spaCy 2.0.0a13
"""
from __future__ import unicode_literals, print_function

import random
from pathlib import Path
import random

import spacy
from spacy.gold import GoldParse, minibatch
from spacy.pipeline import NeuralEntityRecognizer
from spacy.pipeline import TokenVectorEncoder


def get_gold_parses(tokenizer, train_data):
    '''Shuffle and create GoldParse objects'''
    random.shuffle(train_data)
    for raw_text, entity_offsets in train_data:
        doc = tokenizer(raw_text)
        gold = GoldParse(doc, entities=entity_offsets)
        yield doc, gold

 
def train_ner(nlp, train_data, output_dir):
    random.seed(0)
    optimizer = nlp.begin_training(lambda: [])
    nlp.meta['name'] = 'en_ent_animal'
    for itn in range(50):
        losses = {}
        for batch in minibatch(get_gold_parses(nlp.make_doc, train_data), size=3):
            docs, golds = zip(*batch)
            nlp.update(docs, golds, losses=losses, sgd=optimizer, update_shared=True,
                       drop=0.35)
        print(losses)
    if not output_dir:
        return
    elif not output_dir.exists():
        output_dir.mkdir()
    nlp.to_disk(output_dir)


def main(model_name, output_directory=None):
    print("Creating initial model", model_name)
    nlp = spacy.blank(model_name)
    if output_directory is not None:
        output_directory = Path(output_directory)

    train_data = [
        (
            "Horses are too tall and they pretend to care about your feelings",
            [(0, 6, 'ANIMAL')],
        ),
        (
            "Do they bite?", 
            [],
        ),
 
        (
            "horses are too tall and they pretend to care about your feelings",
            [(0, 6, 'ANIMAL')]
        ),
        (
            "horses pretend to care about your feelings",
            [(0, 6, 'ANIMAL')]
        ),
        (
            "they pretend to care about your feelings, those horses",
            [(48, 54, 'ANIMAL')]
        ),
        (
            "horses?",
            [(0, 6, 'ANIMAL')]
        )

    ]
    nlp.pipeline.append(TokenVectorEncoder(nlp.vocab))
    nlp.pipeline.append(NeuralEntityRecognizer(nlp.vocab))
    nlp.pipeline[-1].add_label('ANIMAL')
    train_ner(nlp, train_data, output_directory)

    # Test that the entity is recognized
    text = 'Do you like horses?'
    print("Ents in 'Do you like horses?':")
    doc = nlp(text)
    for ent in doc.ents:
        print(ent.label_, ent.text)
    if output_directory:
        print("Loading from", output_directory)
        nlp2 = spacy.load(output_directory)
        doc2 = nlp2('Do you like horses?')
        for ent in doc2.ents:
            print(ent.label_, ent.text)


if __name__ == '__main__':
    import plac
    plac.call(main)
